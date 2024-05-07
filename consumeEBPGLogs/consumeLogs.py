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
    plt.show()

def loadfile(filepath):
    file = open(filepath,'r', encoding='cp1252')
    logs = file.readlines()
    file.close()

    return logs

def generate_output(log,plot=False):
    output = []
    output.append('Log file: {}'.format(find_input_first('JMAN LOGFILE:',log).rstrip('\n').split(' ')[-1]))

    job_status = find_input_first('Job status',log).rstrip('\n').split(' ')[-1]
    output.append('Job Status: {}'.format(job_status))
    output.append('Using holder: {}'.format(find_input_first('pg select holder',log).rstrip('\n').split(' ')[-1]))
    
    if job_status != 'FINISHED':
        return '\n'.join(output)
    
    output.append('Exposure current: {}nA'.format(float(find_input_first('Beam diameter',log).rstrip('\n').split(':')[-1].rstrip('nA').strip())))
    
    if len(find_input_index('faradaycup reference',log)) == 0:
        output.append('\nFaraday cup NOT used as reference! Is this intentional?\n')
    
    index_write_fields = find_input_index('DATE:',log)
    output.append('Number of write-fields: {}'.format(len(index_write_fields)))
    output.append('Number of write-fields outside the height range: {}'.format(count_failed_height_measurements(index_write_fields,log)))

    if len(index_write_fields) > 1:
        wfX,wfY,heights = get_wf_heights(index_write_fields,log)

        minH,maxH = np.argmin(heights),np.argmax(heights)
        tilt_distance = np.sqrt(np.abs(wfX[minH]-wfX[maxH])**2+np.abs(wfY[minH]-wfY[maxH])**2)
        output.append('Zmin: {:.1f}um, Zmax: {:.1f}um, Tilt: {:.2f}um/mm'.format(heights[minH],heights[maxH],np.abs(heights[minH]-heights[maxH])/tilt_distance))
    
        if plot:
            xlim = np.abs(np.min(wfX)-np.max(wfX))*0.1
            ylim = np.abs(np.min(wfY)-np.max(wfY))*0.1
            zlim = np.abs(np.min(heights)-np.max(heights))*0.1

            fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
            ax.scatter(wfX, wfY, heights, c='r', s=50)
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

def count_failed_height_measurements(indices,log):
    failed = 0
    for index in indices:
        if log[index-1].startswith('%ENG_W_SHOUHM'):
            failed += 1
    
    return failed

def get_wf_heights(indices,log):
    length = len(indices)
    wfX,wfY,heights = np.empty(length),np.empty(length),np.empty(length)
    
    for i,index in enumerate(indices):
        posList = find_input_first('pos', log, lineNum=index).rstrip('\n').split(':')[-1].split(',')
        wfX[i] = float(posList[0].strip().rstrip('_mm'))
        wfY[i] = float(posList[1].strip().rstrip('_mm'))
        heights[i] = float(find_input_first('height', log, lineNum=index).rstrip('\n').split(':')[-1].rstrip('_um'))
    
    wfX = wfX-np.mean(wfX)
    wfY = wfY-np.mean(wfY)
        
    return wfX,wfY,heights

if __name__ == '__main__':
    main()