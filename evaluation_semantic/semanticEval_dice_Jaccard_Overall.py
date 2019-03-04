#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Mar  2 16:06:39 2019

@author: shariba
FileName: semanticEval_dice_Jaccard_Overall.py
"""

import numpy as np

def file_lines_to_list(path):
  # open txt file lines to a list
  with open(path) as f:
    content = f.readlines()
  # remove whitespace characters like `\n` at the end of each line
  content = [x.strip() for x in content]
  return content

def calculate_confusion_matrix_from_arrays(prediction, ground_truth, nr_labels):
    replace_indices = np.vstack((ground_truth.flatten(),prediction.flatten())).T
    confusion_matrix, _ = np.histogramdd(replace_indices, bins=(nr_labels, nr_labels),range=[(0, nr_labels), (0, nr_labels)])
    confusion_matrix = confusion_matrix.astype(np.uint32)
    return confusion_matrix

def calculate_iou(confusion_matrix):
    ious = []
    f2_scores=[]
    for index in range(confusion_matrix.shape[0]):
        true_positives = confusion_matrix[index, index]
        false_positives = confusion_matrix[:, index].sum() - true_positives
        false_negatives = confusion_matrix[index, :].sum() - true_positives
        denom = true_positives + false_positives + false_negatives
        denom_f2 = (5*true_positives + false_positives + 4*false_negatives)
        
        if denom == 0:
            iou = 0
        else:
            iou = float(true_positives) / denom
        
        if denom_f2 == 0:
            f2_score = 0
        else:
            f2_score= (5*true_positives) / denom_f2
        f2_scores.append(f2_score)    
        ious.append(iou)
    return ious, f2_scores

def calculate_dice(confusion_matrix):
    dices = []
    for index in range(confusion_matrix.shape[0]):
        true_positives = confusion_matrix[index, index]
        false_positives = confusion_matrix[:, index].sum() - true_positives
        false_negatives = confusion_matrix[index, :].sum() - true_positives
        denom = 2 * true_positives + false_positives + false_negatives
        if denom == 0:
            dice = 0
        else:
            dice = 2 * float(true_positives) / denom
        dices.append(dice)
    return dices

#F_\beta = \frac {(1 + \beta^2) 
#\cdot \mathrm{true\ positive} }{(1 + \beta^2) \cdot \mathrm{true\ positive} + \beta^2 \cdot \mathrm{false\ negative} + \mathrm{false\ positive}}\,.

def jaccard(y_true, y_pred):
    intersection = (y_true * y_pred).sum()
    union = y_true.sum() + y_pred.sum() - intersection
    return (intersection + 1e-15) / (union + 1e-15)


def dice(y_true, y_pred):
    return (2 * (y_true * y_pred).sum() + 1e-15) / (y_true.sum() + y_pred.sum() + 1e-15)

def get_args():
    
    import argparse
    parser = argparse.ArgumentParser(description="For EAD2019 challenge: semantic segmentation", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--GT_maskDIR", type=str, default="../../semantic_masks/", help="ground truth mask image (5 channel tif image only)")
    parser.add_argument("--Eval_maskDIR", type=str, default="../../semantic_masks/", help="predicted mask image (5 channel tif image only)")
    parser.add_argument("--Result_dir", type=str, default="results", help="predicted mask image (5 channel tif image only)")
    parser.add_argument("--jsonFileName", type=str, default='metrics_semantic.json', help="predicted mask image (5 channel tif image only)")
    
    args = parser.parse_args()
    
    return args

if __name__ == '__main__':
    
    import tifffile as tiff
    import glob
    import os
    
    result_dice = []
    result_jaccard = []
    
    classTypes =  ['Instrument', 'Specularity', 'Artefact' , 'Bubbles', 'Saturation'] 
    
    '''
        By default we have set below images:
        file_name_GT='../masks/0000600_mask.tif'
        file_name_predicted='../masks/0000600_mask.tif'
        
        Pass arguments: python semanticEval_dice_Jaccard.py --GT_maskImage $GroundTruthMask_5channel --Eval_maskImage $YourPredictedMasks_5channel
    '''
    args=get_args()
    ext=['*.tif']
    for filename in sorted(glob.glob(args.GT_maskDIR +ext[0], recursive = True)):
    
        file_name_GT = args.GT_maskDIR+filename.split('/')[-1]
        file_name_eval_maskImage = args.Eval_maskDIR+filename.split('/')[-1] 
        
        y_true_Array = tiff.imread(file_name_GT)
        y_pred_Array = tiff.imread(file_name_eval_maskImage)
        
        confusion_matrix = calculate_confusion_matrix_from_arrays(y_pred_Array, y_true_Array, 5)
        
        dice_= calculate_dice(confusion_matrix)
        
        
        if y_true_Array.shape[0]!=5 or y_pred_Array.shape[0] !=5:
            print('the number of channels in each of GT and predicted mask must be 5, nothing done!!!')
        else:
            dice_val =[]
            jaccard_val=[]
            for i in range(len(classTypes)):
                y_true = (((y_true_Array[i, :, :])> 0).astype(np.uint8))
                y_pred = (((y_pred_Array[i, :, :])> 0).astype(np.uint8))
                result_dice = [dice(y_true.flatten(), y_pred.flatten())]
                result_jaccard = [jaccard(y_true.flatten(), y_pred.flatten())]
                
                dice_val.append(result_dice)
                jaccard_val.append(result_jaccard)
         
        _, f2_score=calculate_iou(confusion_matrix)   
        print('diceval {}'.format(dice_val))
    #    get mean values
        meanDiceVal = np.mean(dice_val)  
        meanJaccard = np.mean(jaccard_val)  
        mean_f2_score = np.mean(f2_score)  
        print('mean dice {} and mean jaccard {} and F2-score{}'.format(meanDiceVal, meanJaccard, mean_f2_score))
        
        
    '''
    creating json file
    '''
    import json
    # TODO: Loop this for 
    imageName = file_name_GT.split('/')[-1]
    my_dictionary = {
        "EADChallenge2019":{
                "dice":{
                 "value":   (meanDiceVal) 
                },
                "jaccard":{
                  "value": (meanJaccard)
                },
                "typeIIerror":{
                  "value": (mean_f2_score)
                },
                "score":{
                  "value": (0.5*meanDiceVal+0.5*meanJaccard),  
                }
                
            }
    }      
    os.makedirs(args.Result_dir, exist_ok=True)
    jsonFileName=os.path.join(args.Result_dir, args.jsonFileName)
    
    #### FIXME: uncomment below lines if you want to delete the existing .json semantic metric file 
#    try:
#        os.remove(jsonFileName)
#    except OSError:
#        pass
    
    ''' Geting Instance score after semantic scores: keep appending all your scores from your sementation method,
        later you combined with mAP to compute the final score for ==> instance sementation (see here: https://ead2019.grand-challenge.org/Evaluation/),
        we wont compare each pixel category but rather just the mAP values that will assure that the algorithm is atleast aware of artefact classes that are present in the images 
    '''
    
    fileObj= open(jsonFileName, "a")
    fileObj.write("\n")
    # w+ or a
    json.dump(my_dictionary, fileObj)
    fileObj.close()
