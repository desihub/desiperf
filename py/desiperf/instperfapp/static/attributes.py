Focalplane_attributes = {
'Observation': ['EXPID','DATE_OBS','TARGTRA','TARGTDEC','SKYRA','SKYDEC','DELTARA','DELTADEC',
        'REQTIME','EXPTIME','FOCUS0','FOCUS1','FOCUS2','FOCUS3','FOCUS4','FOCUS5','AIRMASS',
        'MOUNTHA','ZD','MOUNTAZ','DOMEAZ','S2N','NIGHT','MOONRA','MOONDEC','PARALLACTIC','MOUNTEL'],

'GFA': ['CCDTEMP_MEAN','HOTPELTIER_MEAN','COLDPELTIER_MEAN','FILTER_MEAN','HUMID2_MEAN',
        'HUMID3_MEAN','FPGA_MEAN','CAMERAHUMID_MEAN','CAMERATEMP_MEAN'],

'Guider': ['COMBINED_X','COMBINED_Y','DURATION','SEEING','FRAMES','MEANX','MEANY',
        'MEANX2','MEANY2','MEANXY','MAXX','MAXY'],

'Telescope': ['AIR_FLOW','AIR_TEMP','TRUSS_TEMP','AIR_IN_TEMP','FLOWRATE_IN','MIRROR_TEMP',
        'AIR_DEWPOINT','AIR_OUT_TEMP','DECBORE_TEMP','FLOWRATE_OUT','HINGE_S_TEMP','HINGE_W_TEMP',
        'GLYCOL_IN_TEMP','SERVO_SETPOINT','TOPRING_S_TEMP','TOPRING_W_TEMP','TRUSS_ETB_TEMP',
        'TRUSS_ETT_TEMP','TRUSS_NTB_TEMP','TRUSS_NTT_TEMP', 'TRUSS_STB_TEMP','TRUSS_STS_TEMP',
        'TRUSS_STT_TEMP','TRUSS_TSB_TEMP','TRUSS_TSM_TEMP','TRUSS_TST_TEMP','TRUSS_WTB_TEMP',
        'TRUSS_WTT_TEMP','CASSCAGE_I_TEMP','CASSCAGE_O_TEMP','GLYCOL_OUT_TEMP','MIRROR_AVG_TEMP',
        'MIRROR_EIB_TEMP','MIRROR_EIT_TEMP','MIRROR_EOB_TEMP','MIRROR_EOT_TEMP','MIRROR_NIB_TEMP',
        'MIRROR_NIT_TEMP','MIRROR_NOB_TEMP','MIRROR_NOT_TEMP','MIRROR_RTD_TEMP','MIRROR_SIB_TEMP',
        'MIRROR_SIT_TEMP','MIRROR_SOB_TEMP','MIRROR_SOT_TEMP','MIRROR_WIB_TEMP','MIRROR_WIT_TEMP',
        'MIRROR_WOB_TEMP','MIRROR_WOT_TEMP','PRIMARYCELL_I_TEMP','PRIMARYCELL_O_TEMP','MIRROR_DESIRED_TEMP',
        'CENTERSECTION_I_TEMP','CENTERSECTION_O_TEMP','GUST','SPLIT','DEWPOINT','HUMIDITY','PRESSURE',
        'WIND_SPEED','TEMPERATURE','WIND_DIRECTION','C_FLOOR','SCR_ROOF','PLATFORM',
        'WIND_DIRECTION','LCR_FLOOR','SHACK_WALL','STAIRS_MID','LCR_CEILING', 'STAIRS_LOWER','STAIRS_UPPER',
        'UTILITY_ROOM','LCR_AMBIENT_N','LCR_AMBIENT_S','SHACK_CEILING','TELESCOPE_BASE','UTILITY_N_WALL',
        'DOME_BACK_LOWER','DOME_BACK_UPPER','DOME_LEFT_LOWER','DOME_LEFT_UPPER','SCR_E_WALL_COUDE',
        'SCR_ROOF_AMBIENT','DOME_RIGHT_LOWER','DOME_RIGHT_UPPER','LCR_N_WALL_INSIDE','LCR_W_WALL_INSIDE',
        'LCR_N_WALL_OUTSIDE','LCR_W_WALL_OUTSIDE','SCR_E_WALL_COMPUTER'],
        
'Corrector': ['ROT_RATE','ROT_OFFSET','ROT_INTERVAL','HEX_TRIM_0','HEX_POSITION_0','HEX_TRIM_1',
        'HEX_POSITION_1','HEX_TRIM_2','HEX_POSITION_2','HEX_TRIM_3','HEX_POSITION_3','HEX_TRIM_4', 
        'HEX_POSITION_4','HEX_TRIM_5','HEX_POSITION_5','ADC_NREV1','ADC_NREV2','ADC_ANGLE1','ADC_ANGLE2'],

'FVC': ['TEMP_DEGC', 'EXPTIME_SEC', 'PSF_PIXELS'],

'Positioner': ['MAX_BLIND','MAX_BLIND_95','RMS_BLIND','RMS_BLIND_95','MAX_CORR','MAX_CORR_95',
        'RMS_CORR','RMS_CORR_95']}


Positioner_attributes = {
'Observation': ['EXPID','OBS_X','OBS_Y','PETAL_ID','POS_P','POS_T','PRIMARYCELL_I_TEMP','PRIMARYCELL_O_TEMP',
        'PROBE1_HUMIDITY','PROBE1_TEMP','PROBE2_HUMIDITY','PROBE2_TEMP','PTL_X','PTL_Y', 'PTL_Z',
        'LAST_MEAS_FWHM','LAST_MEAS_OBS_X','LAST_MEAS_OBS_Y','LAST_MEAS_PEAK'],

'Telescope': ['AIR_MIRROR_TEMP_DIFF','AIR_FLOW','AIR_TEMP','TRUSS_TEMP','AIR_IN_TEMP','FLOWRATE_IN',
        'MIRROR_TEMP','AIR_DEWPOINT','AIR_OUT_TEMP','DECBORE_TEMP','FLOWRATE_OUT','HINGE_S_TEMP',
        'HINGE_W_TEMP','GLYCOL_IN_TEMP','SERVO_SETPOINT','GUST','SPLIT','DEWPOINT','HUMIDITY',
        'PRESSURE','WIND_SPEED','TEMPERATURE','WIND_DIRECTION','TELESCOPE_BASE','UTILITY_N_WALL',
        'DOME_BACK_LOWER','DOME_BACK_UPPER','DOME_LEFT_LOWER','DOME_LEFT_UPPER','DOME_RIGHT_LOWER',
        'DOME_RIGHT_UPPER'],

'Positioner': ['FIBERASSIGN_X','FIBERASSIGN_Y','OFFSET_0','OFFSET_FINAL','PETAL_LOC','TARGET_DEC',
        'TARGET_RA','TOPRING_S_TEMP', 'TOPRING_W_TEMP','TOTAL_CREEP_MOVES_P','TOTAL_CREEP_MOVES_T',
        'TOTAL_CRUISE_MOVES_P','TOTAL_CRUISE_MOVES_T','TOTAL_MOVE_SEQUENCES']

}

Spectrograph_attributes = {
'Observation': ['EXPID','TARGTRA','TARGTDEC','SKYRA','SKYDEC','DELTARA','DELTADEC',
        'REQTIME','EXPTIME','FOCUS0','FOCUS1','FOCUS2','FOCUS3','FOCUS4','FOCUS5',
        'AIRMASS','MOUNTHA','ZD','MOUNTAZ','DOMEAZ','TRANSPAR','SKYLEVEL','NIGHT',
        'MOONRA','MOONDEC','PARALLACTIC','MOUNTEL'],

'Spectrograph': ['CAMERA_TEMP','CAMERA_HUMIDITY','BENCH_CRYO_TEMP','BENCH_NIR_TEMP','BENCH_COLL_TEMP',
        'IEB_TEMP'],

'Camera': ['READNOISE','BIAS','COSMICS_RATE','MEANDX','MINDX','MAXDX','MEANDY','MINDY','MAXDY',
        'MEANXSIG', 'MINXSIG', 'MAXXSIG','MEANYSIG','MINYSIG','MAXYSIG','INTEG_RAW_FLUX','MEDIAN_RAW_FLUX','THRU'],

'Shack': ['ROOM_PRESSURE','SPACE_TEMP1','REHEAT_TEMP','SPACE_HUMIDITY','HEATER_OUTPUT','SPACE_TEMP2','SPACE_TEMP4',
        'SPACE_TEMP_AVG','SPACE_TEMP3','COOLING_COIL_TEMP','CHILLED_WATER_OUTPUT']
}
