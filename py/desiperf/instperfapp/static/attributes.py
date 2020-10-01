Focalplane_attributes = {
	'Observation':['EXPID','data_location','targtra','targtdec','skyra','skydec','deltara','deltadec',
	'reqtime','exptime','flavor','program','lead','focus','airmass','mountha','zd','mountaz','domeaz',
	'spectrographs','s2n','transpar','skylevel','zenith','mjd_obs','date_obs','night','moonra','moondec',
	'parallactic','mountel','sequence','obstype'],

	'GFA':['ccdtemp_mean','hotpeltier_mean','coldpeltier_mean','filter_mean','humid2_mean','humid3_mean',
	'fpga_mean','camerahumid_mean','cameratemp_mean'],

	'Guider':['combined_x','combined_y','guider_time_recorded','duration','expid','seeing','frames','meanx','meany',
	'meanx2','meany2','meanxy','maxx','maxy'],

	'Telescope':['air_flow','air_temp','truss_temp','air_in_temp','flowrate_in','mirror_temp','air_dewpoint',
	'air_out_temp','decbore_temp','flowrate_out','hinge_s_temp','hinge_w_temp','glycol_in_temp','servo_setpoint',
	'topring_s_temp','topring_w_temp','truss_etb_temp','truss_ett_temp','truss_ntb_temp','truss_ntt_temp',
	'truss_stb_temp','truss_sts_temp','truss_stt_temp','truss_tsb_temp','truss_tsm_temp','truss_tst_temp',
	'truss_wtb_temp','truss_wtt_temp','casscage_i_temp','casscage_o_temp','glycol_out_temp','mirror_avg_temp',
	'mirror_eib_temp','mirror_eit_temp','mirror_eob_temp','mirror_eot_temp','mirror_nib_temp','mirror_nit_temp',
	'mirror_nob_temp','mirror_not_temp','mirror_rtd_temp','mirror_sib_temp','mirror_sit_temp','mirror_sob_temp',
	'mirror_sot_temp','mirror_wib_temp','mirror_wit_temp','mirror_wob_temp','mirror_wot_temp','primarycell_i_temp',
	'primarycell_o_temp','mirror_desired_temp','telescope_timestamp','centersection_i_temp','centersection_o_temp',
	'gust','split','dewpoint','humidity','pressure','wind_speed','temperature','wind_direction','tower_timstamp',
	'C_floor','SCR_roof','platform','wind_direction','LCR_floor','shack_wall','stairs_mid','LCR_ceiling',
	'stairs_lower','stairs_upper','utility_room','LCR_ambient_N','LCR_ambient_S','shack_ceiling','shutter_lower',
	'shutter_upper','dome_timestamp','telescope_base','utility_N_wall','dome_back_lower','dome_back_upper',
	'dome_left_lower','dome_left_upper','SCR_E_wall_coude','SCR_roof_ambient','dome_right_lower','dome_right_upper',
	'LCR_N_wall_inside','LCR_W_wall_inside','LCR_N_wall_outside','LCR_W_wall_outside','SCR_E_wall_computer'],

	'Corrector':['rot_rate','hex_status','rot_offset','rot_enabled','rot_interval','hex_trim_0','hex_position_0',
	'hex_trim_1','hex_position_1','hex_trim_2','hex_position_2','hex_trim_3','hex_position_3','hex_trim_4',
	'hex_position_4','hex_trim_5','hex_position_5','hex_tweak','adc_home1','adc_home2','adc_nrev1','adc_nrev2',
	'adc_angle1','adc_angle2'],

	'FVC':['shutter_open','fan_on','temp_degc','exptime_sec','psf_pixels','fvc_time_recorded'],

	'Positioner':['MAX_BLIND','MAX_BLIND_95','RMS_BLIND','RMS_BLIND_95','MAX_CORR','MAX_CORR_95','RMS_CORR','RMS_CORR_95']

}

Positioner_attributes = {
	'Observation':['EXPID', 'move_cmd','move_val1','move_val2','obs_x','obs_y','petal_id','pos_id','pos_move_index',
 	'pos_p','pos_t','primarycell_i_temp','primarycell_o_temp','probe1_humidity','probe1_temp','probe2_humidity',
 	'probe2_temp','ptl_x','ptl_y','ptl_z','last_meas_fwhm','last_meas_obs_x','last_meas_obs_y','last_meas_peak',],

	'Telescope':['air_mirror_temp_diff','air_flow','air_temp','truss_temp','air_in_temp','flowrate_in','mirror_temp','air_dewpoint',
	'air_out_temp','decbore_temp','flowrate_out','hinge_s_temp','hinge_w_temp','glycol_in_temp','servo_setpoint',
	'gust','split','dewpoint','humidity','pressure','wind_speed','temperature','wind_direction',
	'telescope_base','utility_N_wall','dome_back_lower','dome_back_upper',
	'dome_left_lower','dome_left_upper','dome_right_lower','dome_right_upper'],

	'Positioner':['FIBERASSIGN_X','FIBERASSIGN_Y','OFFSET_0','OFFSET_FINAL','PETAL_LOC','TARGET_DEC','TARGET_RA','topring_s_temp',
	'topring_w_temp','total_creep_moves_p','total_creep_moves_t', 'total_cruise_moves_p','total_cruise_moves_t','total_move_sequences',]

}

Spectrograph_attributes = {
	'Observation':['EXPID','data_location','targtra','targtdec','skyra','skydec','deltara','deltadec',
	'reqtime','exptime','flavor','program','lead','focus','airmass','mountha','zd','mountaz','domeaz',
	'spectrographs','s2n','transpar','skylevel','zenith','mjd_obs','date_obs','night','moonra','moondec',
	'parallactic','mountel','sequence','obstype'],

	'Spectrograph':['CAMERA_TEMP','CAMERA_HUMIDITY','bench_cryo_temp','bench_nir_temp','bench_coll_temp','ieb_temp'],

	'Camera':['READNOISE','BIAS','COSMICS_RATE','MEANDX','MINDX','MAXDX','MEANDY','MINDY','MAXDY','MEANXSIG',
	'MINXSIG','MAXXSIG','MEANYSIG','MINYSIG','MAXYSIG','INTEG_RAW_FLUX','MEDIAN_RAW_FLUX','MEDIAN_RAW_SNR','FLUX',
 	'SNR','SPECFLUX','THRU'],

 	'Shack':['room_pressure','space_temp1', 'reheat_temp', 'space_humidity','time_recorded', 'heater_output', 
 	'space_temp2', 'space_temp4','space_temp_avg', 'space_temp3', 'cooling_coil_temp','chilled_water_output']
}
