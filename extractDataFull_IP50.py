# This code takes an exported file from the system and the Full Waveform
# data. It then integrates the full waveform data for the new sampling points
# This is written for 4 channels. 

import numpy as np
from scipy import optimize as opt
import pybert as pb
import pygimli as pg
from pybert import tdip
import os
import pandas as pd

#minnum = 1
#maxnum = 133
a = np.arange(1,109)
b = np.arange(110,134)
filenumbers = np.append(a,b)
#filenumbers = np.array([1,2])

funcfit=True

filepart = '0001'
#wavDirectory = 'Plattner50'
#infoDirectory = 'BACKYARD-PLA-50/Rawdata'
wavDirectory = 'Pla50/fullwave'
infoDirectory = 'Pla50/info'
gatesdt =  np.loadtxt('gatesdt.txt') # file with the gates
delay = 0.8 #0.01 #0.8
samprate = 9000 # Sampling rate of the full waveform
# Exported file for differently-set time intervals
preExported = 'BACKYARD-PLA-50_Plattner4andDip_1_data.txt' 

#saveas = 'Backyard-PLA-50-extracted_delay10'
saveas = 'Backyard-PLA-50-extracted'

# The problem here is that BERT doesn't correctly
# read the number of the measurement! It just assumes the
# first row is the first measurement. This of course
# does not work with the numbering of the full waveform data
# To fix this: import the preExported data, sort it by
# measurement number and channel, then save it, then
# import that one in BERT. THIS IS ONLY AN ISSUE WHEN I WANT
# TO USE THE FULL WAVEFORM DATA

df = pd.read_csv(preExported, sep='\t')
dfresort = df.sort_values(['MeasID','Channel'])
dfresort.to_csv('resorted_data.txt', sep='\t')


# Load the preExported data
#ip = tdip.TDIPdata(preExported)
ip = tdip.TDIPdata('resorted_data.txt')
gatesdt =  np.loadtxt('gatesdt.txt')
ip.setGates(dt=gatesdt, delay=delay)


# Need sampling intervals. I approximate the IP signal between them
# by averaging them. These will be associated with the center
# time stamps of the time intervals.
samptimes = np.cumsum(np.append(0,gatesdt)) + delay
sampinds = np.round(samptimes*samprate)
sampinds = sampinds.astype(int)


# I am assuming that the data file is ordered by Measurement, then channel
count = 0

#for num in range(minnum, maxnum+1):
for num in filenumbers:
    print('Working on number %d' %(num))
    filename = '%s-%06d.txt' %(filepart,num)
    fullfile = os.path.join(wavDirectory,filename) 

    # Remove the stupid "{" part from the info file
    infofile = os.path.join(infoDirectory,filename)
    execstring = "sed '/{/d' ./%s > tmpfile.txt" %(infofile)
    os.system(execstring)
    
    # Load the info file to find out which parts are IP. Code 8 is for IP
    info = pd.read_csv('tmpfile.txt', sep='\t')
    ipind = info.iloc[:,1]==8
    steps = info.loc[ipind].iloc[:,0].to_numpy()
    # Detrending info. Code for SPIP is 6
    spind = info.iloc[:,1]==6
    stepZero = info.loc[spind].iloc[:,0].to_numpy()
    
    # If it is odd, remove the last one because it is not bracketed by SPIP
    if np.mod(len(steps),2):
        steps=steps[:-1]
  
    # Load the data file
    #t,Vr1,Vr2,Vr3,Vr4,Vt,It,Step = np.loadtxt(fullfile,skiprows=1,unpack=True)
    # First column is time, then the channels.
    # Last two are transmitter voltage and current, and step codes
    data = pd.read_csv(fullfile, sep='\t')
    # Can access Vr1 as data.iloc[:,1]
    # get number of columns through len(data.columns)
    # If four channels in use, it will have 8 columns
    channels = np.arange(1,len(data.columns)-3)
    Step = data.iloc[:,-1].to_numpy()
    sampnr = np.arange(len(data))
    
    # Go through each of the channel and get Vavg
    for chnum in channels:
        # Vavg is the average time signal over the different IP steps.
        # Each IP step is going to Zero I after having had I stabilize
        chan = data.iloc[:,chnum].to_numpy()

        # Detrend
        chanDet = chan.copy()
        if True:

            if funcfit:
                print('Functional detrending')
                # define exponential function
                def trendfun(x,a,b):
                    return a*np.exp(b*x)
                    #return a*x + b
                    #return a*np.power(x,3) + b*np.power(x,2) + c*x + d
                
                # First get the samplenumbers (x) and voltage values (y)
                x = np.array([])
                y = np.array([])
                for i in range(0,len(stepZero)):
                    inds = Step==stepZero[i]
                    xadd = sampnr[inds]
                    yadd = chan[inds]
                    x = np.append(x,xadd)
                    y = np.append(y,yadd)
                # Now fit function
                p0 = [1,0]
                popt, pcov = opt.curve_fit(trendfun,  x,  y, p0=p0)
                chanDet = chan -  trendfun(sampnr, *popt)
                #popt, pcov = opt.curve_fit(trendfun,  x,  np.log(np.abs(y))) #, p0=p0)
                #chanDet = chan -  np.sign(chan)*np.exp(trendfun(sampnr, *popt))
                
                # The * before popt expands the values
                
            else:
                print('Piecewise linear detrending')
                # Piecewise linear fit
                for i in range(0,len(stepZero)-1):
                    inds1 = Step==stepZero[i]
                    inds2 = Step==stepZero[i+1]
                    x1 = sampnr[inds1]
                    x2 = sampnr[inds2]
                    x = np.append(x1,x2)
                    y1 = chan[inds1]
                    y2 = chan[inds2]
                    y = np.append(y1,y2)
                    # Fit
                    coef = np.polyfit(x,y,1)
                    trendFun = np.poly1d(coef)
                    # Subtract only within the time bracketed by the stepZero
                    inds = np.arange(x1[0], x2[-1])
                    chanDet[inds] = chan[inds] - trendFun(inds)


        
        Vavg = np.zeros(ip.t.shape)
        for stp in steps:
            inds = Step==(stp-1)
            V0 = np.mean(chanDet[inds])

            inds = Step==stp
            V = chanDet[inds]*1000 # turn into mV
            # Calc average of values within interval
            Vint = np.zeros(ip.t.shape)
            for i in range(0,len(sampinds)-1):
                Vint[i] = np.mean(V[sampinds[i]:sampinds[i+1]])
            Vavg = Vavg + Vint/V0

        Vavg = Vavg/len(steps)
        # Replace corresponding row of ip.MA with Vavg
        ip.MA[:,count] = Vavg
        count = count+1;


# Save data file
ip.saveData(basename=saveas)
