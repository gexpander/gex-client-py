import time

import serial
import usb.core
import threading

class BaseGexTransport:
    """ Base class for GEX transports """

    def __init__(self):
        self._listener = None

    def close(self):
        # Tell the thread to shut down
        raise Exception("Not implemented")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ End of a with block, close the thread """
        self.close()

    def __enter__(self):
        """ This is needed for with blocks to work """
        return self

    def write(self, buffer):
        """ Send a buffer of bytes """
        raise Exception("Not implemented")

    def listen(self, listener):
        """ Attach a listener for incoming bytes """
        self._listener = listener

    def poll(self, timeout, testfunc=None):
        """
        Receive bytes until a timeout, testfunc returns True,
        or first data if no testfunc is given
        """
        raise Exception("Not implemented")


class TrxSerialSync (BaseGexTransport):
    """
    Transport based on pySerial, no async support.
    Call poll() to receive spontaneous events or responses.

    This can be used only if EXPOSE_ACM is enabled
    """

    def __init__(self, port='/dev/ttyACM0'):
        """ port - device to open """
        super().__init__()
        self._serial = serial.Serial(port=port, timeout=0.3)

    def close(self):
        # Tell the thread to shut down
        self._serial.close()

    def write(self, buffer):
        """ Send a buffer of bytes """
        self._serial.write(buffer)

    def poll(self, timeout, testfunc=None):
        """
        Receive bytes until a timeout, testfunc returns True,
        or first data if no testfunc is given
        """
        first = True
        attempts = 10
        while attempts > 0:
            rv = bytearray()

            # Blocking read with a timeout
            if first:
                rv.extend(self._serial.read(1))
                first = False

            # Non-blocking read of the rest
            rv.extend(self._serial.read(self._serial.in_waiting))

            if 0 == len(rv):
                # nothing was read
                if testfunc is None or testfunc():
                    # TF is in base state, we're done
                    return
                else:
                    # Wait for TF to finish the frame
                    attempts -= 1
                    first = True
            else:
                if self._listener:
                    self._listener(rv)


class TrxRawUSB (BaseGexTransport):
    """
    pyUSB-based transport with minimal overhead and async IO
    """

    def __init__(self, sn=None):
        """ sn - GEX serial number """
        super().__init__()

        self.dataSem = threading.Semaphore()
        self.dataSem.acquire()

        GEX_ID = (0x0483, 0x572a)

        # -------------------- FIND THE DEVICE ------------------------

        def dev_match(d):
            if (d.idVendor, d.idProduct) != GEX_ID:
                return False

            # Match only by ID if serial not given
            if sn is None:
                return True

            # Reading the S/N can fail with insufficient permissions (wrong udev rules)
            # Note that this error will happen later when configuring the device, too
            try:
                if d.serial_number == sn:
                    return True
            except Exception as e:
                print(e)
                pass

            return False

        dev = usb.core.find(custom_match=dev_match)
        if dev is None:
            raise Exception("Found no matching and accessible device.")
        self._dev = dev

        # -------------------- PREPARE TO CONNECT ---------------------

        # If the ACM interface is visible (not 255), the system driver may be attached.
        # Here we tear that down and expose the raw endpoints

        def detach_kernel_driver(dev, iface):
            if dev.is_kernel_driver_active(1):
                try:
                    dev.detach_kernel_driver(1)
                except usb.core.USBError as e:
                    raise Exception("Could not detach kernel driver from iface %d: %s" % (iface, str(e)))

        # EP0 - control
        # EP1 - VFS in/out
        # EP2 - CDC data in/out
        # EP3 - CDC control

        detach_kernel_driver(dev, 2)  # CDC data
        detach_kernel_driver(dev, 3)  # CDC control

        # Set default configuration
        # (this will fail if we don't have the right permissions)
        dev.set_configuration()

        # We could now print the configuration
        #cfg = dev.get_active_configuration()

        # ----------------------- RX THREAD ---------------------------

        # The reception is done using a thread.
        # It ends when _ending is set True
        self._ending = False

        def worker():
            while not self._ending:
                try:
                    resp = self._dev.read(0x82, 64, 100)
                    if self._listener is not None:
                        self._listener(bytearray(resp))
                        self.dataSem.release() # notify we have data
                except usb.USBError:
                    pass # timeout

        t = threading.Thread(target=worker)
        t.start()

        # Save a reference for calling join() later
        self._thread = t

    def close(self):
        # Tell the thread to shut down
        self._ending = True
        self._thread.join()

    def write(self, buffer):
        """ Send a buffer of bytes """
        self._dev.write(0x02, buffer, 100)

    def poll(self, timeout, testfunc=None):
        # Using time.sleep() would block for too long. Instead we release the semaphore on each Rx chunk of data
        # and then check if it's what we wanted (let TF handle it and call the listener)
        start = time.time()
        while (time.time() - start) < timeout:
            self.dataSem.acquire(True, 0.1)
            if testfunc is None or testfunc():
                break
        pass

