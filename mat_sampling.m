% this is an example of sampling the ADC from Matlab and then plotting a
% FFT graph. The ADC unit called 'adc' is configured to use PA1 as Ch. 0

%transport = py.gex.TrxSerialThread(pyargs('port', '/dev/ttyUSB1', 'baud', 57600));
transport = py.gex.TrxRawUSB();
client = py.gex.Client(transport);
adc = py.gex.ADC(client, 'adc');

L=1000;
Fs=1000;

adc.set_sample_rate(uint32(Fs));
data = adc.capture(uint32(L));
data = double(py.array.array('f',data));

Y = fft(data);
P2 = abs(Y/L);
P1 = P2(1:L/2+1);
P1(2:end-1) = 2*P1(2:end-1);

f = Fs*(0:(L/2))/L;
plot(f,P1)

client.close()
