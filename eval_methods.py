import pandas as pd
import json
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sn
import os

from project_annotation import Annotation

def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path) as f:
            data = json.load(f)
            return data
    else:
        print("Error: can't find path",file_path)
        return None
    
LABELS_SHL = {
        0: "Null",
        1: "Still",
        2: "Walking",
        3: "Run",
        4: "Bike",
        5: "Car",
        6: "Bus",
        7: "Train",
        8: "Subway",
        }

class Anno:
    # Total number of samples
    samples_total_dict = {'A': 4620201, 'B': 4557401, '0': 172701}
    
    def __init__(self, path, scenario):
        self.path = path
        self.scenario = scenario
        
        self.anno_dic = load_json(self.path)
        self.anno_obj = Annotation(type_=f"anno_{self.scenario}", path_=None, points=self.anno_dic)
        self.anno_mat = self.anno_obj.get_array( last_sample=self.samples_total_dict[self.scenario], convert_to_idx=True )
        
    @property
    def samples_total(self): return self.samples_total_dict[self.scenario]

def calc_F1Score(label,pred):
    # Total number of samples
    N = label.shape[0]

    F1 = 0
    for i in range(9):
        ni_l = np.sum((label == i))
        ni_p = np.sum((pred == i))

        if ni_l == 0:
            continue

        # weight
        wi = ni_l/N

        TP = np.sum((label == i) & (pred == i))
        FP = np.sum((label != i) & (pred == i))
        FN = np.sum((label == i) & (pred != i))

        if TP == 0:
            continue

        pi = (TP)/(TP+FP)
        ri = (TP)/(TP+FN)

        Fi = 2*(pi*ri)/(pi+ri)
        #print(f"Class {i} {Fi=} {ni_l=} {ni_p=} {TP=} {FP=} {FN=} {pi=} {ri=}")

        F1 += wi * Fi

    return F1

CARPM_indeces = {i:v for i,v in enumerate(["TP","TN","Overfill","Underfill","Merge","Fragmentation","Insertion","Deletion","Substitution"])}
#print(CARPM_indeces)

def mark_null_puddles(signal_A, signal_B, results, fill_value):
    s = 0
    l = -1
    for i in range(1,results.shape[0]):
        
        c = signal_A[i-1]
        
        # New actual class
        if signal_A[i] != c:
            
            # Search coherent activity for fragmentations
            if c != 0:
                sp = None
                for j in range(s,i):
                    if signal_B[j] == c:
                        if signal_B[j-1] == 0: 
                            if sp is not None:
                                results[sp+1:j] = fill_value
                        sp = j
                    elif signal_B[j] != 0:
                        sp = None
                        
            s = i
    return results

def calc_CARPM(label,pred):
    
    res = np.empty_like(label)
    res.fill(-1)

    
    # Insertion
    res[np.logical_and.reduce((label!=pred,label==0,pred!=0))] = 6
    
    # Deletion
    res[np.logical_and.reduce((label!=pred,label!=0,pred==0))] = 7
    
    
    # ~~~~~~~~~~~~~~~ #
    #  Special Cases  #
    # ~~~~~~~~~~~~~~~ #
    
    # Merge
    res = mark_null_puddles(signal_A=pred, signal_B=label, results=res, fill_value=4)
    
    # Fragmentation
    res = mark_null_puddles(signal_A=label, signal_B=pred, results=res, fill_value=5)

    
    # Overfill/Underfill
    s, sp = 0, 0
    for i in range(1,res.shape[0]):

        # Synced start can be skipped
        if label[i] != label[i-1] and pred[i] != pred[i-1]:
            s = i
            sp = i
            continue
        
        
        # Only consider cases where match is reached and no merge/fragmentation is already marked
        if label[i] == pred[i] and res[i-1] not in (4,5):
        
            # New actual activity class (Overfill)
            if label[i] != label[i-1] and label[i] != 0:
                # print(i,"Overfill")
                res[sp:i] = 2

            # End actual activity class (Underfill) +
            if label[i] != label[i-1] and label[i] == 0 and pred[sp-1] == label[i-1]:   
                # print(i,"Underfill+")
                res[sp:i] = 3

            # New predicted activity class (Underfill)
            if pred[i] != pred[i-1] and pred[i] != 0:
                # print(i,"Underfill")
                res[s:i] = 3

            # End predicted activity class (Overfill) +
            if pred[i] != pred[i-1] and pred[i] == 0 and label[s-1] == pred[i-1]:
                # print(i,"Overfill+")
                res[s:i] = 2
            
                      
        # ~~~~~~~~~~~~~~~ #
        #  Start Indeces  #
        # ~~~~~~~~~~~~~~~ #
    
        # New actual class
        if label[i] != label[i-1]:
            s = i
        
        # New predicted class
        if pred[i] != pred[i-1]:
            sp = i
    
    # True Positives  
    res[np.logical_and(label==pred,label!=0)] = 0
    
    # True Negatives
    res[np.logical_and(label==pred,label==0)] = 1
    
    # Substitution
    res[np.logical_and.reduce((label!=pred,label!=0,pred!=0))] = 8
    
    return res

class GroundTruth:
    
    def __init__(self, path, scenario):
        self.path = path
        self.scenario = scenario
        self.anno = Anno(self.path, self.scenario)

    # Calculate weighted F1 score
    def get_F1(self, anno_pred, max_sample):
        
        label = self.anno.anno_mat[:max_sample]
        pred = anno_pred.anno_mat[:max_sample]
        
        return calc_F1Score(label, pred)
    
    # Calculate Continuous Activity Recognition Performance Metrics
    def get_CARPM(self, anno_pred=None, carpm=None, max_sample=0):
        assert anno_pred is not None or carpm is not None
        
        if carpm is None:
            label = self.anno.anno_mat[:max_sample]
            pred = anno_pred.anno_mat[:max_sample]

            carpm = calc_CARPM(label,pred)

        total = {v:np.sum(carpm==i) for i,v in CARPM_indeces.items()}
        ratio = {k:v/max_sample for k,v in total.items()}
        
        return total, ratio, carpm
    
import re
from sklearn.metrics import confusion_matrix

def get_sec(time_str):
    """Get seconds from time."""
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def get_cm(label,pred,labels):
    return np.round(confusion_matrix(y_true=label,y_pred=pred,labels=labels,normalize='all'), 3)
    

path_pred = "static/uploads/pred"
class Task:
    GT = {'A': GroundTruth(path=os.path.join(path_pred,"anno_270417.json"), scenario='A'),
          'B': GroundTruth(path=os.path.join(path_pred,"anno_270417.json"), scenario='B'),
          '0': GroundTruth(path=os.path.join(path_pred,"anno_SHL_test.json"), scenario='0')}

    def __init__(self, path, scenario, load_carpm=True):
        self.path = path
        self.scenario = scenario

        if scenario == '0':
            self.settings = load_json(os.path.join(path,"settings.json"))
            #self.tlx = load_json(os.path.join(path,f"TLX_{scenario}.json"))

            self.log_path = os.path.join(path,"log_js.txt")
            self.carpm_path = os.path.join(path,"carpm.npy")

            self.anno = Anno( os.path.join(path,"anno.json"), scenario )
            
        else:
            self.settings = load_json(os.path.join(path,scenario,"settings.json"))
            self.tlx = load_json(os.path.join(path,f"TLX_{scenario}.json"))

            self.log_path = os.path.join(path,scenario,"log_js.txt")
            self.carpm_path = os.path.join(path,scenario,"carpm.npy")

            self.anno = Anno( os.path.join(path,scenario,"anno.json"), scenario )
            
        
        self.comp = self.get_completion_rate()
        self.F1score = self.GT[self.scenario].get_F1(anno_pred=self.anno, max_sample=self.max_sample)
        
        if load_carpm and os.path.exists(self.carpm_path):
            self.CARPM = self.GT[self.scenario].get_CARPM(carpm=self.load_carpm(), max_sample=self.max_sample)
        else:
            self.CARPM = self.GT[self.scenario].get_CARPM(anno_pred=self.anno, max_sample=self.max_sample)
            self.save_carpm()
            
    @property
    def carpm(self):
        return self.CARPM[2]
    
    @property
    def final_time(self):
        return int(self.comp['end_time']/self.comp['ratio_sighted'])
    
    @property
    def max_sample(self):
        return self.comp['max_sample']
    
    @property
    def samples_total(self): return self.anno.samples_total
    
    @property
    def AI(self):
        return self.settings["modus"]["AI"]
    
    def save_carpm(self):
        np.save(file=self.carpm_path, arr=self.carpm, allow_pickle=False, fix_imports=False)
    
    def load_carpm(self):
        return np.load(file=self.carpm_path, mmap_mode=None, allow_pickle=False, fix_imports=False)
    
    # Ratio how much of the material was covered
    # To DO: Add time to complete?
    def get_completion_rate(self):
        
        # Find maximum sample viewed
        max_sample = 0
        
        # Establish time it took to sight maximum sample and do last annotation
        start_time = '00:00:00'
        sight_time = '00:00:00'
        anno_time = '00:00:00'
        end_time = '00:00:00'
        
        with open(self.log_path, 'r') as f:
            for i,line in enumerate(f):
                end_time = line.split()[1]
                if i==0:
                    start_time = line.split()[1]
                    
                # Check for sighted material
                result = re.search("\[Canvas\] Start: .+ Stop: .+ Selected:",line)
                if result is not None:
                    stop = int(result.group().split()[-2])
                    if stop > max_sample:
                        max_sample = stop
                        sight_time = line.split()[1]
                        
                # Check for annotation
                result = re.search("\[Anno\] Add",line)
                if result is not None:
                    anno_time = line.split()[1]
                    
        sight_time = get_sec(sight_time) - get_sec(start_time)
        anno_time = get_sec(anno_time) - get_sec(start_time)
        end_time = get_sec(end_time) - get_sec(start_time)
        
        max_sample = min(max_sample,self.samples_total)
        
        return {
                'max_sample': max_sample,
                'ratio_sighted': max_sample / self.samples_total,
                'start_time': start_time,
                'sight_time': sight_time,
                'anno_time': anno_time,
                'end_time': min(1200,end_time),
               }
    
    @property
    def confusion_matrix(self):
        
        label = self.GT[self.scenario].anno.anno_mat[:self.max_sample]
        pred = self.anno.anno_mat[:self.max_sample]
        
        return get_cm(label,pred,labels=list(range(9)))
        
    # Generate the confusion matrix for substituted classes
    @property
    def substitution_matrix(self):
        
        label = self.GT[self.scenario].anno.anno_mat[:self.max_sample]
        pred = self.anno.anno_mat[:self.max_sample]
        carpm = self.carpm
        
        label = label[carpm==8]
        pred = pred[carpm==8]
        
        return get_cm(label,pred,labels=list(range(1,9)))
    
class Participant:
    def __init__(self, path):
        assert os.path.exists(path)
        
        self.task = { "A": Task(path,"A"),
                      "B": Task(path,"B") }
        
        self.signup = load_json(os.path.join(path,"signup.json"))
        self.quest = load_json(os.path.join(path,"questionnaire.json"))
        
    @property
    def AI_first(self):
        return self.task["A"].AI
    
    def get_att(self, att):
        return self.signup[att]
    
class Study:
    def __init__(self, result_path):
        self.parts = {name: Participant(os.path.join(result_path,name)) for name in os.listdir(result_path)}
        
    def get_att(self, att):
        return { k: v.get_att(att) for k,v in self.parts.items()  }

def plot_cm(cm,title="test", substitution=False):
    labels = [LABELS_SHL[idx] for idx in list(range(1 if substitution else 0, 9))]
    
    fig = plt.figure(figsize = (7,7))

    df_cm = pd.DataFrame(cm, index=labels, columns=labels)
    ax = sn.heatmap(df_cm, cmap=sn.cubehelix_palette(as_cmap=True), annot=True, cbar=False, square=True, fmt='.3f') #vmin=0, vmax=1, 
    ax.set_xlabel("Predicted Activity")
    ax.set_ylabel("Actual Activity")
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(os.path.join("img","CM_"+title.replace(" ","_")+".pdf"), bbox_inches = 'tight')
    return fig