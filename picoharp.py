'''
Created on Apr 1, 2014

@author: esbarnard
'''

from ScopeFoundry import HardwareComponent
try:
    from equipment.pypicoharp import PicoHarp300
except Exception as err:
    print "could not load modules for PicoHarp:", err
    
class PicoHarpHardwareComponent(HardwareComponent):

    def setup(self):
        self.name = "picoharp"
        self.debug = True
        
        self.count_rate0 = self.add_logged_quantity("count_rate0", dtype=int, ro=True, vmin=0, vmax=100e6)
        self.count_rate1 = self.add_logged_quantity("count_rate1", dtype=int, ro=True, vmin=0, vmax=100e6)
        self.mode = self.add_logged_quantity("Mode", dtype=str, choices=[("HIST","HIST"),("T2","T2"),("T3","T3")], initial='HIST')


        self.add_logged_quantity("Tacq", dtype=int, unit="ms", vmin=1, vmax=100*60*60*1000)
        self.add_logged_quantity("Binning", dtype=int, choices=[(str(x), x) for x in range(0,8)])
        self.add_logged_quantity("Resolution", dtype=int, unit="ps", ro=True, si=False)

        self.add_logged_quantity("SyncDivider", dtype=int, choices=[("1",1),("2",2),("4",4),("8",8)])
        self.add_logged_quantity("SyncOffset", dtype=int, vmin=-99999, vmax=99999, si=False)
        
        self.add_logged_quantity("CFDLevel0", dtype=int, unit="mV", vmin=0, vmax=800, si=False)
        self.add_logged_quantity("CFDZeroCross0", dtype=int,  unit="mV", vmin=0, vmax=20, si=False)
        self.add_logged_quantity("CFDLevel1", dtype=int, unit="mV", vmin=0, vmax=800, si=False)
        self.add_logged_quantity("CFDZeroCross1", dtype=int, unit="mV", vmin=0, vmax=20, si=False)

        self.add_logged_quantity("stop_on_overflow", dtype=bool)
        
        self.histogram_channels = self.add_logged_quantity("histogram_channels", dtype=int, ro=False, vmin=0, vmax=2**16, initial=2**16, si=False)

    def connect(self):
        if self.debug: print "Connecting to PicoHarp"
        
        # Open connection to hardware
        
        print self.mode.val
        
        PH = self.picoharp = PicoHarp300(devnum=0, mode = self.mode.val, debug=False)

        # connect logged quantities
        
        LQ = self.settings.as_dict()
        
        LQ["count_rate0"].hardware_read_func = PH.read_count_rate0
        LQ["count_rate1"].hardware_read_func = PH.read_count_rate1
        
        LQ["Binning"].updated_value.connect(lambda x, LQ=LQ: LQ["Resolution"].read_from_hardware() )
        
        
        LQ["Tacq"].hardware_set_func         = PH.set_Tacq
        LQ["Tacq"].hardware_read_func        = lambda PH=PH: PH.Tacq
        
        LQ["Binning"].hardware_set_func      = PH.write_Binning
        LQ["Binning"].hardware_read_func     = lambda PH=PH: PH.Binning

        LQ["Resolution"].hardware_read_func     = PH.read_Resolution
        
        LQ["SyncDivider"].hardware_set_func  = PH.write_SyncDivider
        LQ["SyncDivider"].hardware_read_func = lambda PH=PH: PH.SyncDivider
        
        LQ["SyncOffset"].hardware_set_func   = PH.write_SyncOffset
        LQ["SyncOffset"].hardware_read_func = lambda PH=PH: PH.SyncOffset
        
        LQ["CFDLevel0"].hardware_set_func    = PH.write_CFDLevel0
        LQ["CFDLevel0"].hardware_read_func = lambda PH=PH: PH.CFDLevel[0]
        
        LQ["CFDZeroCross0"].hardware_set_func  = PH.write_CFDZeroCross0
        LQ["CFDZeroCross0"].hardware_read_func = lambda PH=PH: PH.CFDZeroCross[0]
        
        LQ["CFDLevel1"].hardware_set_func    = PH.write_CFDLevel1
        LQ["CFDLevel1"].hardware_read_func   = lambda PH=PH: PH.CFDLevel[1]
        
        LQ["CFDZeroCross1"].hardware_set_func  = PH.write_CFDZeroCross1
        LQ["CFDZeroCross1"].hardware_read_func = lambda PH=PH: PH.CFDZeroCross[1]

        LQ["stop_on_overflow"].hardware_set_func = PH.write_stop_overflow
        LQ["stop_on_overflow"].update_value(True)
        
        
        #connect logged quantities to other gui widgets
        
        
        # initial settings
        self.picoharp.setup_experiment() # sets all the defaults
        
        # read initial information
        self.read_from_hardware()
        
        
        
        if self.debug: print "Done Connecting to PicoHarp"
        
        
    def disconnect(self):
        #disconnect hardware
        self.picoharp.close()
        
        for lq in self.logged_quantities.values():
            lq.hardware_read_func = None
            lq.hardware_set_func = None
        
        #clean up hardware object
        del self.picoharp