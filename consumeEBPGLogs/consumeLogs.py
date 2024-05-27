import argparse
import matplotlib.pyplot as plt
import numpy as np

def main():
    # handle CLI args
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', required=True, help='path to logfile')
    parser.add_argument('-p', '--plot', required=False, action='store_true', help='pass flag to plot heightmap')
    args = parser.parse_args()

    # read logfile
    logs = loadfile(args.file)

    # generate_output
    output = generate_output(logs,plot=args.plot)

    print(output)
    if args.plot:
        plt.show()

def loadfile(filepath):
    file = open(filepath,'r', encoding='cp1252')
    logs = file.readlines()
    file.close()

    return list(map(str.strip, logs))

def generate_output(log,plot=False):
    output = []
    output.append('Log file: {}'.format(find_input_first('JMAN LOGFILE:',log).rstrip('\n').split(' ')[-1]))

    job_status = find_input_first('Job status',log).rstrip('\n').split(' ')[-1]
    output.append('Job Status: {}'.format(job_status))

    output.append('Exposure Time: {}'.format(find_input_first('Elapsed time:',log).rstrip('\n').split(' ')[-1]))
    output.append('Using holder: {}'.format(find_input_first('pg select holder',log).rstrip('\n').split(' ')[-1]))
    
    output.append('Exposure current: {}nA'.format(float(find_input_first('Beam diameter',log).rstrip('\n').split(':')[-1].rstrip('nA').strip())))

    pre_marker = find_input_first('cjob_align (pre)',log).rstrip('\n')
    if len(pre_marker) > 0:
        pre_pos = find_input_first('pre  align marker',log).rstrip('\n').split(':')[1].split(',')[0:2]
        output.append('Pre-marker alignment selected. Marker @ {:.2f}um,{:.2f}um'.format(*list(map(float, pre_pos))))

    global_markers = find_input_index('cjob_align (first set)',log)
    if len(global_markers) > 0:
        average_rot = find_input_first('average rotation angle',log,lineNum=global_markers[0]).rstrip('\n').split('=')[1].split('(')[0]
        output.append('Chip rotation: {:.3f}deg'.format(float(average_rot)*180.0/np.pi))

    if job_status != 'FINISHED':
        # try to do get some info that might be helpful

        # check if the -f flag was set
        if len(find_input_index('faradaycup reference',log)) == 0:
            output.append('Faraday cup NOT used as reference! Is this intentional?')
        
        # check if any write fields were written
        index_write_fields = find_input_index('DATE:',log)
        output.append('Number of write-fields written before crash: {}'.format(len(index_write_fields)))

        return '\n'.join(output)
    
    if len(find_input_index('faradaycup reference',log)) == 0:
        output.append('Faraday cup NOT used as reference! Is this intentional?')
    
    index_write_fields = find_input_index('DATE:',log)
    wfX,wfY,heights,meas_ok = get_wf_heights(index_write_fields,log)

    output.append('Number of write-fields: {:d}'.format(len(index_write_fields)))
    output.append('Number of write-fields outside the height range: {:d}'.format(len(index_write_fields)-np.sum(meas_ok,dtype='int')))

    h_ok = np.nonzero(meas_ok == 1)
    h_Nok = np.nonzero(meas_ok == 0)
    if len(index_write_fields) > 1:
        heights_ok = heights[h_ok]
        wfX_ok,wfY_ok = wfX[h_ok],wfY[h_ok]
        minH,maxH = np.argmin(heights_ok),np.argmax(heights_ok)
        tilt_distance = np.sqrt(np.abs(wfX_ok[minH]-wfX_ok[maxH])**2+np.abs(wfY_ok[minH]-wfY_ok[maxH])**2)
        output.append('Zmin: {:.1f}um, Zmax: {:.1f}um, Tilt: {:.2f}um/mm'.format(heights_ok[minH],heights_ok[maxH],np.abs(heights_ok[minH]-heights_ok[maxH])/tilt_distance))
    
    if plot:
        xlim = np.abs(np.min(wfX)-np.max(wfX))*0.1
        ylim = np.abs(np.min(wfY)-np.max(wfY))*0.1
        zlim = np.abs(np.min(heights)-np.max(heights))*0.1

        fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
        ax.scatter(wfX[h_ok], wfY[h_ok], heights[h_ok], c='tab:green', s=50)
        ax.scatter(wfX[h_Nok], wfY[h_Nok], heights[h_Nok], c='tab:red', s=50)
        ax.set_xlim([np.min(wfX)-xlim,np.max(wfX)+xlim])
        ax.set_ylim([np.min(wfY)-ylim,np.max(wfY)+ylim])
        ax.set_zlim([np.min(heights)-zlim,np.max(heights)+zlim])
        ax.set_xlabel('X [mm]')
        ax.set_ylabel('Y [mm]')
        ax.set_zlabel('Z [um]')

        fig.tight_layout()
        plt.show(block=False)

    return '\n'.join(output)

def find_input_first(input_start, log, lineNum=0):
    found_line = ''
    for index,line in start_with_generator(input_start, log, lineNum):
        found_line = line
        break
    
    return found_line

def start_with_generator(string, log, lineNum):
    log_reduced = log[lineNum:]
    for index,line in enumerate(log_reduced):
        if line.startswith(string):
            yield index,line

def find_input_index(input_start, log, lineNum=0):
    indices = []
    for index,line in start_with_generator(input_start, log, lineNum):
        indices.append(index)

    return indices

def height_measurement_ok(index,log):
    height_ok = 1
    if log[index-1].startswith('%ENG_W_'):
        height_ok = 0 
    return height_ok

def get_wf_heights(indices,log):
    length = len(indices)
    wfX,wfY,heights,meas_ok = np.empty(length),np.empty(length),np.empty(length),np.empty(length)
    
    for i,index in enumerate(indices):
        posList = find_input_first('pos', log, lineNum=index).rstrip('\n').split(':')[-1].split(',')
        wfX[i] = float(posList[0].strip().rstrip('_mm'))
        wfY[i] = float(posList[1].strip().rstrip('_mm'))
        meas_ok[i] = height_measurement_ok(index,log)
        heights[i] = float(find_input_first('height', log, lineNum=index).rstrip('\n').split(':')[-1].rstrip('_um'))
    
    wfX = wfX-np.mean(wfX)
    wfY = wfY-np.mean(wfY)
        
    return wfX,wfY,heights,meas_ok

if __name__ == '__main__':
    main()