#!/usr/bin/python3
import usb.core
import usb.util

# based on the docs for the AG Series Waveform Generator SCPI Protocol
# tested on the AG2052F at revspace
# MIT licensed, see LICENSE

WRITE_EP = 0x03
READ_EP = 0x81

Functions = [
'SINE', 'SQUare', 'RAMP', 'PULSe', 'NOISe', 'ARB', 'DC',
'AM', 'FM', 'PM', 'FSK', 'PWM', 'SWEep', 'BURSt'
]

class OwonAG:
    def __init__(self, debugen=False):
        self.debug = debugen
        self.dev = usb.core.find(idVendor=0x5345, idProduct=0x1234)
        if self.dev is None:
            raise ValueError('Device not found')
        self.dev.reset()

        self.dev.set_configuration()
        cfg = self.dev.get_active_configuration()
        intf = cfg[(0,0)]
        usb.util.claim_interface(self.dev, intf)
        self.dev.clear_halt(READ_EP)
        self.dev.clear_halt(WRITE_EP)

        identity = self.readCmd("*IDN?").split(",")
        if identity[0] != "OWON" or identity[1][:2] != "AG":
            print("Warning: may not be Owon AG, got: " + str(identity))

    def sendCmd(self, cmd, isReading=False):
        self.dev.write(WRITE_EP, cmd + '\n')
        if (not isReading) and self.debug:
            try:
                s = self.read()
                if len(s) and s != 'NULL':
                    print("unexpected output after %s: %s" % (cmd, repr(s)))
            except usb.core.USBError:
                pass

    def read(self):
        self.dev.clear_halt(READ_EP)
        op = self.dev.read(READ_EP, 1024)
        op = ''.join([chr(x) for x in op])
        op = op.split('\n')
        if op[-1] == '': op = op[:-1]
        if op[-1] == '->': op = op[:-1]
        if len(op) == 1: op = op[0]
        return op

    def readCmd(self, cmd):
        self.sendCmd(cmd, isReading=True)
        return self.read()

    def reset(self):        
        self.sendCmd("*RST")

    def setChannel(self, ch):
        assert ch in [0,1]
        self.sendCmd(":CHANnel CH%d" % (ch + 1,))

    def setFunction(self, func):
        self.sendCmd(":FUNCtion %s" % (func,))

    # integer for ohms, or False/OFF for high-z
    def setLoad(self, func, load):
        if load == True:
            load = "ON"
        elif load == False:
            load = "OFF"
        cmd = ":FUNCtion:%s:LOAD %s" % (func, str(load))
        if load == "ON" or load == "OFF":
            s = self.readCmd(cmd) # returns ON/OFF
        else:
            self.sendCmd(cmd)

    # frequency in hz
    def setFrequency(self, func, val):
        cmd = ":FUNCtion:%s:FREQuency %s" % (func, str(val))
        s = self.readCmd(cmd)

    # period in seconds
    def setPeriod(self, func, val):
        cmd = ":FUNCtion:%s:PERiod %s" % (func, str(val))
        s = self.readCmd(cmd)

    # amplitude in Vpp
    def setAmplitude(self, func, val):
        cmd = ":FUNCtion:%s:AMPLitude %s" % (func, str(val))
        self.sendCmd(cmd)

    # offset in volts
    def setOffset(self, func, val):
        cmd = ":FUNCtion:%s:OFFset %s" % (func, str(val))
        #s = self.readCmd(cmd)
        self.sendCmd(cmd)

    # high voltage level
    def setHighV(self, func, val):
        cmd = ":FUNCtion:%s:HIGHt %s" % (func, str(val))
        self.sendCmd(cmd)

    # low voltage level
    def setLowV(self, func, val):
        cmd = ":FUNCtion:%s:LOW %s" % (func, str(val))
        self.sendCmd(cmd)

    # duty cycle as percentage (square/pulse)
    def setDutyCycle(self, func, val):
        cmd = ":FUNCtion:%s:DTYCycle %s" % (func, str(val))
        self.sendCmd(cmd)

    # symmetry in percentage (ramp)
    def setSymmetry(self, func, val):
        cmd = ":FUNCtion:%s:SYMMetry %s" % (func, str(val))
        #self.sendCmd(cmd)
        s = self.readCmd(cmd)

    # pulse width in seconds (pulse)
    def setPulseWidth(self, func, val):
        cmd = ":FUNCtion:%s:WIDTh %s" % (func, str(val))
        self.sendCmd(cmd)

    # :FUNCtion:ARB:BUILtinwform {<name of build-in wave>|<number of build-in wave>}
    def setBuiltInWaveform(self, val):
        cmd = ":FUNCtion:ARB:BUILtinwform %s" % val
        self.sendCmd(cmd)

    # TODO: below here: not so well tested and/or unimplemented :)

    # :FUNCtion:ARB:FILE {<file name>}

    # :FUNCtion:DC:VOLTage {<voltage>}

    # :FUNCtion:{AM|FM|PM|PWM}:SHAPe {<SINE|SQUare|RAMP|NOISe|ARB>}
    # :FUNCtion:{AM|FM|PM|PWM}:FREQuency {<modulating frequency>}
    # :FUNCtion:AM:DEPTh {<depth percent>}
    # :FUNCtion:{AM|FM|PM|FSK|PWM}:SOURce {INTernal|EXTernal}
    # :FUNCtion:FM:DEViation {<frequency deviation>}
    # :FUNCtion:PM:PHASe {<phase deviation>}
    # :FUNCtion:FSK:RATE {<rate>}
    # :FUNCtion:FSK:HOPFreq {<frequency>}
    # :FUNCtion:FSK:DEViation {<width deviation>}

    # :FUNCtion:SWEep:SWEeptime {<sweep time>}
    def setSweepTime(self, val):
        cmd = ":FUNCtion:SWEep:SWEeptime %s" % str(val)
        self.sendCmd(cmd)

    # :FUNCtion:SWEep:SPACing {LINear|LOGarithmic}
    def setSweepSpacing(self, val):
        cmd = " %s" % str(val)
        self.sendCmd(cmd)

    # :FUNCtion:SWEep:STARtfreq {<start frequency>}
    def setSweepStartFreq(self, val):
        cmd = ":FUNCtion:SWEep:STARtfreq %s" % str(val)
        self.sendCmd(cmd)

    # :FUNCtion:SWEep:STOPfreq {<stop frequency>}
    def setSweepStopFreq(self, val):
        cmd = ":FUNCtion:SWEep:STOPfreq %s" % str(val)
        self.sendCmd(cmd)

    # :FUNCtion:SWEep:CENTrefreq {<center frequency>}
    def setSweepCentreFreq(self, val):
        cmd = ":FUNCtion:SWEep:CENTrefreq %s" % str(val)
        self.sendCmd(cmd)

    # :FUNCtion:SWEep:SPAN {<frequency span>}
    def setSweepSpan(self, val):
        cmd = ":FUNCtion:SWEep:SPAN %s" % str(val)
        self.sendCmd(cmd)

    # :FUNCtion:SWEep:SOURce {INTernal|EXTernal|MANual}
    def setSweepSource(self, val):
        cmd = ":FUNCtion:SWEep:SOURce %s" % str(val)
        self.sendCmd(cmd)

    # :FUNCtion:SWEep:TRIGger 1
    def setSweepTriggerOnce(self):
        cmd = ":FUNCtion:SWEep:TRIGger 1"
        self.sendCmd(cmd)

    # :FUNCtion:BURSt:PERiod {<burst period>}
    # :FUNCtion:BURSt:PHASe {<start phase>}
    # :FUNCtion:BURSt:MODE { NCYCles|GATed}
    # :FUNCtion:BURSt:NCYCle {<cycle number>}
    # :FUNCtion:BURSt:INFinite {CYCLes|INFinite }
    # :FUNCtion:BURSt:POLarity { POSitive | NEGative }
    # :FUNCtion:BURSt:SOURce { INTernal|EXTernal|MANual}

    def setBurstTriggerOnce(self):
        cmd = ":FUNCtion:BURSt:TRIGger 1"
        self.sendCmd(cmd)

    # :FILE:UPLoad <uploading file size>,<uploading file name>
    # :FILE:DOWNload <downloading file name>
    # :FILE:FILEname?
    # :FILE:DELete < file name to be deleted>

    # :SYSTem:VERSion?
    # :SYSTem:CLKSrc {INTernal|EXTernal}
    # :SYSTem:LANGuage {SIMPchinese|TRADchinese|ENGLish}
    # :CHANnel:CH1{ON|OFF|1|0}

    # :COUNter:FREQuency?
    # :COUNter:DTYCycle?
    # :COUNter:COUPling {AC|DC}
    # :COUNter:SENSitivity {LOW,MIDD,HIGH}
    # :COUNter:HFR {ON|OFF}
    # :COUNter:TRIGlev <trigger level>

def printAllWaveforms(ag):
    for w in range(45):
        ag.setBuiltInWaveform(str(w))
        print(ag.readCmd(":FUNCtion:ARB:BUILtinwform?"))

if __name__ == "__main__":
    ag = OwonAG(True)

    #print(ag.readCmd(":SYSTem:VERSion?"))
    #ag.setFunction("SQUare")
    #ag.setLoad("SQUare", False)
    #ag.setFrequency("SQUare", 500000)
    ag.setOffset("SQUare", 0.2)
    ag.setOffset("SQUare", 0.2)
    ag.setOffset("SQUare", 0.2)
    #ag.setHighV("SQUare", 3.3)
    #ag.setLowV("SQUare", 1.2)
    #ag.setAmplitude("SQUare", 2)
    #ag.setPeriod("SQUare", 0.01)
    #ag.setDutyCycle("SQUare", 30)
    #ag.setSymmetry("RAMP", 10)
    #ag.setPulseWidth("PULSe", 0.003)

    import time
    ag.setFunction("SQUare")
    ag.setFunction("SWEep")
    off = 0
    for n in range(300000, 330000, 10000):
        ag.setOffset("SQUare", off)
        ag.setAmplitude("SQUare", 2 - off)
        ag.setSweepCentreFreq(n)
        off = off + 0.1
        time.sleep(0.05)

    printAllWaveforms(ag)

