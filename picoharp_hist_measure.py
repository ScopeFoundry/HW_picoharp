from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import numpy as np
import time

# TODO Needs conversion to python 3, pyqtgraph etc

class PicoHarpHistogramMeasure(Measurement):    
    name = "picoharp_histogram"
    
    hardware_requirements = ['picoharp']
    
    def setup(self):
        self.display_update_period = 0.1 #seconds

        S = self.settings
#         self.stored_histogram_channels = self.add_logged_quantity(
#                                       "stored_histogram_channels", 
#                                      dtype=int, vmin=1, vmax=2**16, initial=2**16)
#         self.stored_histogram_channels.connect_bidir_to_widget(
#                                            self.gui.ui.trpl_live_stored_channels_doubleSpinBox)
        
        S.New('save_h5', dtype=bool, initial=True)
        
        # hardware
        ph = self.picoharp = self.app.hardware['picoharp']

        
        # UI 
        self.ui_filename = sibling_path(__file__,"picoharp_hist_measure.ui")
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.setWindowTitle(self.name)
        
        
        #connect events
        S.progress.connect_bidir_to_widget(self.ui.progressBar)
        self.ui.start_pushButton.clicked.connect(self.start)
        self.ui.interrupt_pushButton.clicked.connect(self.interrupt)
        
        ph.settings.Tacq.connect_bidir_to_widget(self.ui.picoharp_tacq_doubleSpinBox)
        ph.settings.histogram_channels.connect_bidir_to_widget(self.ui.histogram_channels_doubleSpinBox)
        
        S.save_h5.connect_bidir_to_widget(self.ui.save_h5_checkBox)
        #self.gui.ui.picoharp_acquire_one_pushButton.clicked.connect(self.start)
        #self.gui.ui.picoharp_interrupt_pushButton.clicked.connect(self.interrupt)
    
    def setup_figure(self):
        self.fig = self.gui.add_figure("picoharp_live", self.gui.ui.picoharp_plot_widget)
                    
        self.ax = self.fig.add_subplot(111)
        self.plotline, = self.ax.semilogy([0,20], [1,65535])
        self.ax.set_ylim(1e-1,1e5)
        self.ax.set_xlabel("Time (ns)")
        self.ax.set_ylabel("Counts")
    
    def _run(self):
        ph = self.picoharp = self.gui.picoharp_hc.picoharp
        #: type: ph: PicoHarp300
        
        #FIXME
        #self.plotline.set_xdata(ph.time_array*1e-3)
        sleep_time = np.min((np.max(0.1*ph.Tacq*1e-3, 0.010), 0.100)) # check every 1/10 of Tacq with limits of 10ms and 100ms
        print "sleep_time", sleep_time, np.max(0.1*ph.Tacq*1e-3, 0.010)
        
        ph.start_histogram()
        while not ph.check_done_scanning():
            if self.interrupt_measurement_called:
                break
            ph.read_histogram_data()
            time.sleep(sleep_time)

        ph.stop_histogram()
        ph.read_histogram_data()
        #FIXME
        #self.plotline.set_ydata(ph.histogram_data)

        #print "elasped_meas_time (final):", ph.read_elapsed_meas_time()
        
        save_dict = {
                     'time_histogram': ph.histogram_data,
                     'time_array': ph.time_array,
                     'elapsed_meas_time': ph.read_elapsed_meas_time()
                    }               

                    

        for lqname,lq in self.gui.logged_quantities.items():
            save_dict[lqname] = lq.val
        
        for hc in self.gui.hardware_components.values():
            for lqname,lq in hc.logged_quantities.items():
                save_dict[hc.name + "_" + lqname] = lq.val
        
        for lqname,lq in self.logged_quantities.items():
            save_dict[self.name +"_"+ lqname] = lq.val



        self.fname = "%i_picoharp.npz" % time.time()
        np.savez_compressed(self.fname, **save_dict)
        print "TRPL Picoharp Saved", self.fname
                
        #is this right place to put this?
        self.measurement_state_changed.emit(False)
        if not self.interrupt_measurement_called:
            self.measurement_sucessfully_completed.emit()
        else:
            self.measurement_interrupted.emit()        

               
    def update_display(self):
        ph = self.picoharp
        self.plotline.set_data(ph.time_array*1e-3, ph.histogram_data)
        self.fig.canvas.draw()
