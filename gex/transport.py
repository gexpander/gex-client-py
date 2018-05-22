import time

import serial
import usb.core
import threading
import gex




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


class DongleAdapter(BaseGexTransport):
    def __init__(self, transport, slave):
        # TODO change to allow multiple clients binding to the same adapter
        super().__init__()
        self._transport = transport
        self._slaveAddr = slave
        self._address = None
        transport.listen(self._handleRx)

        self.gw_reset()
        self.gw_add_nodes([slave])

        print('Dongle network prefix: ' +
              ':'.join(['%02X' % x for x in self.gw_get_net_id()]))

    def _handleRx(self, frame):
        if len(frame) != 64:
            raise Exception("Frame len not 64")

        pp = gex.PayloadParser(frame)
        frame_type = pp.u8()

        if frame_type == 1:
            # network address report
            self._address = list(pp.blob(4))
        elif frame_type == 2:
            slave_addr = pp.u8()
            pld_len = pp.u8()
            pld = pp.blob(pld_len)

            # print("Rx chunk(%d): %s" % (pld_len, pld))

            if slave_addr == self._slaveAddr:
                if self._listener is not None:
                    self._listener(pld)

    def close(self):
        self._transport.close()

    def write(self, buffer):
        # multipart sending
        pb = gex.PayloadBuilder()
        # pb.u8(0x47)
        # pb.u8(0xB8)
        pb.u8(ord('m'))
        pb.u8(self._slaveAddr)
        pb.u16(len(buffer))

        ck = 0
        for c in buffer:
            ck ^= c
        ck = 0xFF & ~ck

        pb.u8(ck)

        start = 0
        spaceused = len(pb.buf)
        fits = min(64-spaceused, len(buffer))
        pb.blob(buffer[start:fits])
        if (spaceused + fits) < 64:
            pb.zeros(64 - (spaceused + fits))
        start += fits

        buf = pb.close()
        self._transport.write(buf)

        while start < len(buffer):
            pb = gex.PayloadBuilder()
            fits = min(64, len(buffer) - start)
            pb.blob(buffer[start:start+fits])
            start += fits

            if fits < 64:
                pb.zeros(64 - fits)

            buf = pb.close()
            self._transport.write(buf)

    def listen(self, listener):
        self._listener = listener

    def poll(self, timeout, testfunc=None):
        self._transport.poll(timeout, testfunc)

    def gw_reset(self):
        pb = gex.PayloadBuilder()
        # pb.u8(0x47)
        # pb.u8(0xB8)
        pb.u8(ord('r'))
        spaceused = len(pb.buf)
        pb.zeros(64 - spaceused)
        self._transport.write(pb.close())

    def gw_add_nodes(self, nodes):
        pb = gex.PayloadBuilder()
        # pb.u8(0x47)
        # pb.u8(0xB8)
        pb.u8(ord('n'))
        pb.u8(len(nodes))

        for n in nodes:
            pb.u8(n)

        spaceused = len(pb.buf)
        pb.zeros(64 - spaceused)
        self._transport.write(pb.close())

    def gw_get_net_id(self):
        if self._address is not None:
            # lazy load
            return self._address

        pb = gex.PayloadBuilder()
        # pb.u8(0x47)
        # pb.u8(0xB8)
        pb.u8(ord('i'))
        spaceused = len(pb.buf)
        pb.zeros(64 - spaceused)
        self._transport.write(pb.close())

        self.poll(0.5, lambda: self._address is not None)
        return self._address


class TrxSerialSync (BaseGexTransport):
    """
    Transport based on pySerial, no async support.
    Call poll() to receive spontaneous events or responses.

    This can be used only if EXPOSE_ACM is enabled, or when GEX is connected
    using a USB-serial adaptor
    """

    def __init__(self, port='/dev/ttyACM0', baud=115200, timeout=0.3):
        """ port - device to open """
        super().__init__()
        self._serial = serial.Serial(port=port, baudrate=baud, timeout=timeout)

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


class TrxSerialThread (BaseGexTransport):
    """
    Transport based on pySerial, running on a thread.

    This can be used only if EXPOSE_ACM is enabled, or when GEX is connected
    using a USB-serial adaptor
    """

    def __init__(self, port='/dev/ttyACM0', baud=115200, timeout=0.2):
        """ port - device to open """
        super().__init__()
        self._serial = serial.Serial(port=port, baudrate=baud, timeout=timeout)

        self.dataSem = threading.Semaphore()
        self.dataSem.acquire()

        # ----------------------- RX THREAD ---------------------------

        # The reception is done using a thread.
        # It ends when _ending is set True
        self._ending = False

        def worker():
            while not self._ending:
                try:
                    resp = self._serial.read(max(1, self._serial.in_waiting))
                    if len(resp) and self._listener is not None:
                        self._listener(bytearray(resp))
                        self.dataSem.release()  # notify we have data
                except usb.USBError:
                    pass  # timeout

        t = threading.Thread(target=worker)
        t.start()

        # Save a reference for calling join() later
        self._thread = t

    def close(self):
        # Tell the thread to shut down
        self._ending = True
        self._thread.join()
        self._serial.close()

    def write(self, buffer):
        """ Send a buffer of bytes """
        self._serial.write(buffer)

    def poll(self, timeout, testfunc=None):
        """
        Receive bytes until a timeout, testfunc returns True,
        or first data if no testfunc is given
        """

        start = time.time()
        while (time.time() - start) < timeout:
            self.dataSem.acquire(True, 0.1)
            if testfunc is None or testfunc():
                break


class TrxRawUSB (BaseGexTransport):
    """
    pyUSB-based transport with minimal overhead and async IO
    """

    def __init__(self, sn=None, remote=False):
        """ sn - GEX serial number """
        super().__init__()

        self.dataSem = threading.Semaphore()
        self.dataSem.acquire()

        GEX_ID = (0x1209, 0x4c61 if remote else 0x4c60)

        self.EP_IN = 0x81 if remote else 0x82
        self.EP_OUT = 0x01 if remote else 0x02
        self.EP_CMD = 0x82 if remote else 0x83

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
            if dev.is_kernel_driver_active(1):#fixme iface is not used??
                try:
                    dev.detach_kernel_driver(1)
                except usb.core.USBError as e:
                    raise Exception("Could not detach kernel driver from iface %d: %s" % (iface, str(e)))

        # EP0 - control
        # EP1 - VFS in/out
        # EP2 - CDC data in/out
        # EP3 - CDC control

        detach_kernel_driver(dev, self.EP_IN&0x7F)  # CDC data
        detach_kernel_driver(dev, self.EP_CMD&0x7F)  # CDC control

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
                    resp = self._dev.read(self.EP_IN, 64, 100)
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
        usb.util.dispose_resources(self._dev)

    def write(self, buffer):
        """ Send a buffer of bytes """
        self._dev.write(self.EP_OUT, buffer, 100)

    def poll(self, timeout, testfunc=None):
        # Using time.sleep() would block for too long. Instead we release the semaphore on each Rx chunk of data
        # and then check if it's what we wanted (let TF handle it and call the listener)
        start = time.time()
        while (time.time() - start) < timeout:
            self.dataSem.acquire(True, 0.1)
            if testfunc is None or testfunc():
                break
        pass

