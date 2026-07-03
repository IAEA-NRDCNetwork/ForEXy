#!/usr/bin/python3
ver="2026.06.24"
############################################################
# DICJ2T Ver.2026.06.24
# (Converter from JSON Dictionary to Trans Dictionary)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
############################################################
import argparse
import datetime
import json
import operator
import os
import re
import time

def dicj2t():
  args=get_args(ver)
  main(*get_input(args))


def main(dict_ver,dir_json,dir_trans,force0):
  time_start=time.time()

  global dict_json
  force=force0
  
  dict_json=dict()

  dictionary_list=[
  "001",  "002", "003", "004", "005", "006", "007", "008",
  "015",  "016", "017", "018", "019",
  "020",  "021", "022", "023", "024", "025", "026",
  "030",  "031", "032", "033", "034", "035", "037", "038",
  "043",  "045", "047", "048", "049",
  "052", 
  "113",  "144",
  "207",  "209", "213", "227", "235", "236"]


# Read JSON Dictionary
  file_in=dir_json+"/dict_"+dict_ver+".json"
  if os.path.exists(file_in):
    f=open(file_in, 'r')
    dict_json=json.load(f)
    f.close()
  else:
    msg="File "+file_in+" does not exist."
    line=""
    print_error_fatal(msg,line)

  if dict_json["transmission_id"]!=dict_ver:
    msg="The dictionary version of the JSON dictionary is not "+dict_ver+"."
    line=""
    print_error_fatal(msg,line)


# Produce TRANS Dictionary
  print("printing trans dictionary   ... ", end="")
  file_out=dir_trans+"/trans."+dict_ver
  ndict=0
  for dict_id in dictionary_list:
    ndict+=1
    if dict_id!="026":
      print(dict_id , end=" ")
      json_to_trans(dict_ver,file_out,dict_id,ndict)
  print("950")
  json_to_trans(dict_ver,file_out,"950",ndict)

  time_end=time.time()
  time_elapsed=format(time_end-time_start, ".2f")
  print("DICJ2T: Processing terminated normally. "+time_elapsed+" sec.\n")


def print_trans(f,char,dict_id,flag80,nline):
  char+="90001"+dict_id+str(nline).zfill(5)+flag80+"\n"
  f.write(char)
  nline+=1
  return nline


def print_long_expansion_trans(f,long_expansion,dict_id,flag80,nline):
  long_expansion="("+long_expansion+")"
  chars=list(long_expansion) 

  if dict_id=="236":
    text="                      "
    text1="                      "
  else:
    text="           "
    text1="           "
  for i,char in enumerate(chars):
    text+=char
#   text0=""
    text1+=char
    if len(text)>66:
      text0="%-66s" % text0
      nline=print_trans(f,text0,dict_id,flag80,nline)
      text=text1
    elif i==len(chars)-1:
      text="%-66s" % text
      nline=print_trans(f,text,dict_id,flag80,nline)
      text=""
    elif chars[i+1]==" ":
      text0=text 
      if dict_id=="236":
        text1="                      "
      else:
        text1="           "
 
  if len(text)!=0:
    text="%-66s" % text
    nline=print_trans(f,text,dict_id,flag80,nline)
 
  return nline


def json_to_trans(dict_ver,file_out,dict_id,ndict):
  expansion_paren=["002", "003", "005", "007", "016", "017",
                   "018", "019", "020", "021", "022", "023",
                   "033", "035", "037", "038", "207", "209",
                   "236"]
  status_trans={"CIN":"!", "EXT":"X", "INT":"!", "OBS":"O",
                "PRE":"!", "PRO":"!", "TRA":" "}
  alteration_trans={"A": "I", "M": "C", "S": "S", " ": " "}

  time=datetime.datetime.now()
  time_out=time.strftime("%Y%m%d")
  if dict_id=="001":
    f=open(file_out,'w')
    char="%-11s" % "TRANS"\
        +"%11s"  % dict_ver\
        +"%11s"  % time_out\
        +" "*33\
        +"9000000000000 "\
        +"\n"
    f.write(char)

    char="%-11s" % "DICTION"\
        +"%11s"  % "90001"\
        +"%11s"  % time_out\
        +" "*33\
        +"9000100000000 "\
        +"\n"
    f.write(char)

  else:
    f=open(file_out,'a')

  nline=1
  num=int(dict_id)+90001000
  char="%-11s" % "SUBDICT"\
      +"%11s"  % num\
      +"%11s"  % time_out\
      +" "\

  if dict_id=="950":
    char+="%-32s" % "List of Dictionaries"
  else:
    ind=get_index("950",dict_id)
    char+="%-32s" % dict_json["950"][ind]["dictionary_name"]
  nline=print_trans(f,char,dict_id," ",nline)

  dictionary_resort(dict_id)

  for record in dict_json[dict_id]:
    code=get_code(dict_id,record)
    ind=get_index(dict_id,code)

    if dict_id=="950":
      flag80=" "
      if record["dictionary_identification_number"]=="026": # Family flag is not in TRANS dictionary
        continue
    else:
      if code=="":
        flag80=" "
      else:
        alteration_flag=dict_json[dict_id][ind]["alteration_flag"]
#       if alteration_flag=="D":
#         continue
        status_code=dict_json[dict_id][ind]["status_code"]
        if status_code=="DEL" or status_code=="INT" or\
           status_code=="PRE" or status_code=="PRO":
          continue
        flag80=status_trans[status_code]
        if flag80==" ":
          flag80=alteration_trans[alteration_flag]

    if code=="": # comment at the top of DICTION
      if dict_id=="236":
        reaction_type0=""
      if dict_id=="016":
        san_field_flag0=""
      else:
        for comment in dict_json[dict_id][ind]["comment"]:
          if type(comment)==dict:
            if dict_id=="006" or dict_id=="007":
              comment=comment["comment_flag"]+comment["comment"]
            else:
              comment=comment["comment"]
          char=" "*11\
              +"%-55s" % comment
          nline=print_trans(f,char,dict_id," ",nline)
      continue

    if dict_id in expansion_paren:
      expansion="("+dict_json[dict_id][ind]["expansion"]+")"
    elif dict_id=="008":
      expansion="("+dict_json[dict_id][ind]["element_name"]+")"
    elif dict_id=="950":
      expansion=dict_json[dict_id][ind]["dictionary_name"]
    elif dict_id!="047" and dict_id!="049" and dict_id!="227":
      expansion=dict_json[dict_id][ind]["expansion"]

    if dict_id=="002":
      char=json_to_trans_002(ind,code,expansion)

    elif dict_id=="004":
      char=json_to_trans_004(ind,code,expansion)

    elif dict_id=="005":
      char=json_to_trans_005(ind,code,expansion)

    elif dict_id=="006":
      char=json_to_trans_006(ind,code,expansion)

    elif dict_id=="008":
      char=json_to_trans_008(ind,code,expansion)

    elif dict_id=="015":
      char=json_to_trans_015(ind,code,expansion)

    elif dict_id=="016":
      (char,san_field_flag0,nline)=\
       json_to_trans_016(ind,code,expansion,san_field_flag0,f,nline)

    elif dict_id=="018" or dict_id=="019" or\
         dict_id=="021" or dict_id=="022" or\
         dict_id=="023" or dict_id=="032":
      if nline==2:
        special_use_flag0=""
      (char,special_use_flag0,nline)=\
       json_to_trans_gen(ind,code,expansion,special_use_flag0,dict_id,f,nline)

    elif dict_id=="024":
      if nline==2:
        data_type_flag_10=""
      (char,data_type_flag_10,nline)=\
       json_to_trans_024(ind,code,expansion,data_type_flag_10,f,nline)

    elif dict_id=="025":
      if nline==2:
        sorting_flag0=dict_json["025"][ind]["sorting_flag"]
      (char,sorting_flag0,nline)=\
       json_to_trans_025(ind,code,expansion,sorting_flag0,f,nline)

    elif dict_id=="033":
      char=json_to_trans_033(ind,code,expansion)

    elif dict_id=="034":
      if nline==2:
        GENQ_flag0=dict_json[dict_id][ind]["general_quantity_modifier_flag"]
      (char,comment_flag,GENQ_flag0,nline)=\
       json_to_trans_034(ind,code,expansion,GENQ_flag0,f,nline)

    elif dict_id=="045":
      char=json_to_trans_045(ind,code,expansion)

    elif dict_id=="047":
      char=json_to_trans_047(ind,code)

    elif dict_id=="048":
      char=json_to_trans_048(ind,code,expansion)

    elif dict_id=="049":
      char=json_to_trans_049(ind,code)

    elif dict_id=="144":
      char=json_to_trans_144(code,expansion)

    elif dict_id=="213":
      char=json_to_trans_213(ind,code,expansion)

    elif dict_id=="227":
      char=json_to_trans_227(ind,code)

    elif dict_id=="235":
      char=json_to_trans_235(ind,code,expansion)

    elif dict_id=="236":
      (char,expansion2,expansion3,reaction_type0,nline)=\
       json_to_trans_236(ind,code,expansion,reaction_type0,flag80,f,nline)

    elif dict_id=="950":
      char=json_to_trans_950(code,expansion)

    else:
      char="%-11s" % code\
          +"%-55s" % expansion
    
    nline=print_trans(f,char,dict_id,flag80,nline)

    if dict_id=="236": # 2nd line of normal expansion
      if expansion2!="":
        char=" "*22\
            +"%-44s" % expansion2
        nline=print_trans(f,char,dict_id,flag80,nline)
      if expansion3!="":
        char=" "*22\
            +"%-44s" % expansion3
        nline=print_trans(f,char,dict_id,flag80,nline)



    if dict_id=="005" or dict_id=="007" or dict_id=="207" or dict_id=="236":
       long_expansion=dict_json[dict_id][ind]["long_expansion"]
       if long_expansion!="":
         nline=print_long_expansion_trans\
                 (f,long_expansion,dict_id,flag80,nline)


    elif dict_id=="227":
       explanation=dict_json[dict_id][ind]["explanation"]
       if explanation!="":
         char=" "*13\
             +"%-21s" % explanation\
             +" "*32
         nline=print_trans(f,char,dict_id,flag80,nline)


    if dict_id!="950":
      for i, comment in enumerate(dict_json[dict_id][ind]["comment"]):
        if dict_id=="034" and comment_flag=="*" and i==0:
          continue
        if type(comment)==dict:
          if dict_id=="002" or dict_id=="005" \
          or dict_id=="016" or dict_id=="034":
            comment=comment["comment"]
          else:
            comment=comment["comment_flag"]+comment["comment"]
        if dict_id=="236":
          char=" "*22\
              +"%-44s" % comment
        else:
          char=" "*11\
              +"%-55s" % comment
        nline=print_trans(f,char,dict_id,flag80,nline)

  N1=nline-2
  char="%-11s"  % "ENDSUBDICT"\
        +"%11s" % N1\
        +"%11s" % 0\
        +" "*33\
        +"90001"+dict_id\
        +"99999 "\
        +"\n"
  f.write(char)

  if dict_id=="950":
    char="%-11s" % "ENDDICTION"\
        +"%11s" % ndict\
        +"%11s" % 0\
        +" "*33\
        +"9000199999999 "\
        +"\n"
    f.write(char)

    char="%-11s" % "ENDTRANS"\
        +"%11s" % 1\
        +"%11s" % 0\
        +" "*33\
        +"9999999999999 "\
        +"\n"
    f.write(char)

  f.close()
  return


def dictionary_resort(dict_id):
# Special sorting
  if dict_id=="006":
    ind=get_index("006","") # comment
    dict_json["006"][ind]["institute_code"]=""
    dict_json["006"]=sorted(dict_json["006"],key=operator.itemgetter("institute_code","code"))

  elif dict_id=="016":
    ind=get_index("016","") # comment
    dict_json["016"][ind]["subentry_number_field_flag"]=""
    dict_json["016"]=sorted(dict_json["016"],key=operator.itemgetter("subentry_number_field_flag"))

  elif dict_id=="018" or dict_id=="019" or\
       dict_id=="021" or dict_id=="022" or\
       dict_id=="023":
    dict_json[dict_id]=sorted(dict_json[dict_id],key=operator.itemgetter("special_use_flag","code"))

  elif dict_id=="024":
    for record in dict_json["024"]:
      code=get_code(dict_id,record)
      ind=get_index("024",code)
      if dict_json["024"][ind]["data_type_flag_1"]==0: # 0 must after 9
        dict_json["024"][ind]["data_type_flag_1a"]="A"
      else:
        dict_json["024"][ind]["data_type_flag_1a"]=str(dict_json["024"][ind]["data_type_flag_1"])

      if dict_json["024"][ind]["data_type_flag_2"] is None: # avoid None in sorting
        dict_json["024"][ind]["data_type_flag_2a"]="0"
      else:
        dict_json["024"][ind]["data_type_flag_2a"]=str(dict_json["024"][ind]["data_type_flag_2"])

      if dict_json["024"][ind]["family_flag"]==" ":
        dict_json["024"][ind]["family_flag_a"]="Z"
      else:
        dict_json["024"][ind]["family_flag_a"]=dict_json["024"][ind]["family_flag"]

# The sorting implemented by DAN2X4 is unclear!!!
      if dict_json["024"][ind]["data_type_flag_1"]==2:

        if dict_json["024"][ind]["plotting_flag_5"]==4:
          dict_json["024"][ind]["plotting_flag_5a"]=1
        elif dict_json["024"][ind]["plotting_flag_5"]==5:
          dict_json["024"][ind]["plotting_flag_5a"]=1
        else:
          dict_json["024"][ind]["plotting_flag_5a"]=dict_json["024"][ind]["plotting_flag_5"]
        if dict_json["024"][ind]["plotting_flag_6"]==4:
          dict_json["024"][ind]["plotting_flag_6a"]=1
        elif dict_json["024"][ind]["plotting_flag_6"]==5:
          dict_json["024"][ind]["plotting_flag_6a"]=1
        else:
          dict_json["024"][ind]["plotting_flag_6a"]=dict_json["024"][ind]["plotting_flag_6"]
      else:
        dict_json["024"][ind]["plotting_flag_5a"]=dict_json["024"][ind]["plotting_flag_5"]
        dict_json["024"][ind]["plotting_flag_6a"]=dict_json["024"][ind]["plotting_flag_6"]

    if dict_json["024"][ind]["data_type_flag_1"]==1 or\
       dict_json["024"][ind]["data_type_flag_1"]==2:
      dict_json["024"]=sorted(dict_json["024"],key=operator.itemgetter(\
         "data_type_flag_1a","data_type_flag_2a","plotting_flag_6a","plotting_flag_5a","keyword"))
    else:
      dict_json["024"]=sorted(dict_json["024"],key=operator.itemgetter(\
         "data_type_flag_1a","data_type_flag_2a","plotting_flag_6a","plotting_flag_5a","family_flag_a","keyword"))

  elif dict_id=="025":
      dict_json["025"]=sorted(dict_json["025"],key=operator.itemgetter(\
         "sorting_flag","unit_family_code","keyword"))

  elif dict_id=="034":
      dict_json["034"]=sorted(dict_json["034"],key=operator.itemgetter(\
         "general_quantity_modifier_flag"))

  elif dict_id=="236":
    for record in dict_json["236"]:
      code=record["code"]
      ind=get_index("236",code)

      if code=="":
        continue

      reaction_type=dict_json["236"][ind]["reaction_type_code"]
      jnd=get_index("213",reaction_type)
      sorting_flag=dict_json["213"][jnd]["sorting_flag"]
      dict_json["236"][ind]["sorting_flag"]=sorting_flag

    ind=get_index("236","") # comment
    dict_json["236"][ind]["sorting_flag"]=-1
    dict_json["236"]=sorted(dict_json["236"],key=operator.itemgetter("sorting_flag"))

  return


def json_to_trans_002(ind,code,expansion):
  char="%-10s" % code\
      +" "\
      +"%-27s" % expansion\
      +" "*10\
      +"%-1s" % dict_json["002"][ind]["keyword_required"]\
      +"%2s"  % dict_json["002"][ind]["internal_numerical_equivalent"]\
      +"%-1s" % dict_json["002"][ind]["code_required"]\
      +"% 3s" % dict_json["002"][ind]["pointer_to_related_dictionary"]\
      +" "*11
  char=char.replace("None", "   ")

  return char


def json_to_trans_004(ind,code,expansion):
  short_expansion="("+dict_json["004"][ind]["short_expansion"]+")"
  pointer=dict_json["004"][ind]["pointer_to_related_dictionary"]
  if pointer is None:
    pointer="      "
  else:
    pointer="DICT"+"%2s" % str(pointer)[-2:].strip()
  char="%-1s"   % code\
      +" "*10\
      +"%-6s"   % short_expansion\
      +" "\
      +"%-35s"  % expansion\
      +" "*2\
      +"%-6s"   % pointer\
      +" "*5

  return char


def json_to_trans_005(ind,code,expansion):
  char="%-6s"  % code\
      +" "*5\
      +"%-50s" % expansion\
      +" "\
      +"%1s"   % dict_json["005"][ind]["area_code"]\
      +"%-3s"  % dict_json["005"][ind]["country_code"]

  return char


def json_to_trans_006(ind,code,expansion):
  char="%-11s" % code\
      +"%-48s" % expansion\
      +"%-7s"  % dict_json["006"][ind]["institute_code"]

  return char


def json_to_trans_008(ind,code,expansion):
  zsymb=code+"-"+dict_json["008"][ind]["element_symbol"]
  char="%-6s" % zsymb\
      +" "*5\
      +"%-22s" % expansion\
      +" "*33

  return char


def json_to_trans_015(ind,code,expansion):
  short_expansion="("+dict_json["015"][ind]["short_expansion"]+")"
  char="%-1s"   % code\
      +" "*10\
      +"%-17s"  % short_expansion\
      +" "\
      +"%-37s"  % expansion\

  return char


def json_to_trans_016(ind,code,expansion,san_field_flag0,f,nline):
  san_field_flag=dict_json["016"][ind]["subentry_number_field_flag"]
  if san_field_flag!=san_field_flag0:
    jnd=get_index("016","")
    for comment in dict_json["016"][jnd]["comment"]:
      comment_flag=comment["comment_flag"]
      comment=comment["comment"]
      if san_field_flag==comment_flag:
        char=" "*11\
            +"%-55s" % comment
        nline=print_trans(f,char,"016"," ",nline)
    san_field_flag0=san_field_flag

  char="%-11s" % code\
      +"%-54s" % expansion\
      +"%-1s"  % san_field_flag

  return char,san_field_flag0,nline


def json_to_trans_gen(ind,code,expansion,special_use_flag0,dict_id,f,nline):
  if nline==2:
    char=" "*11+"="*55
    nline=print_trans(f,char,dict_id," ",nline)
    char=" "*11+"%-55s" % "General use"
    nline=print_trans(f,char,dict_id," ",nline)
    char=" "*11+"="*55
    nline=print_trans(f,char,dict_id," ",nline)
  else:
    special_use_flag=dict_json[dict_id][ind]["special_use_flag"]
    if special_use_flag!=special_use_flag0:
      char=" "*11+"="*55
      nline=print_trans(f,char,dict_id," ",nline)
      if special_use_flag=="NEUT":
        char=" "*11+"%-55s" % "Neutron data only"
        nline=print_trans(f,char,dict_id," ",nline)
      elif special_use_flag=="PHOT":
        char=" "*11+"%-55s" % "Photonuclear data only"
        nline=print_trans(f,char,dict_id," ",nline)
      elif special_use_flag=="FY":
        char=" "*11+"%-55s" % "Fission product yields"
        nline=print_trans(f,char,dict_id," ",nline)
      elif special_use_flag=="GAM":
        char=" "*11+"%-55s" % "Gamma detectors"
        nline=print_trans(f,char,dict_id," ",nline)
      elif special_use_flag=="NEU":
        char=" "*11+"%-55s" % "Neutron detectors"
        nline=print_trans(f,char,dict_id," ",nline)
      elif special_use_flag=="RP":
        char=" "*11+"%-55s" % "Resonance parameter analysis"
        nline=print_trans(f,char,dict_id," ",nline)
      char=" "*11+"="*55
      nline=print_trans(f,char,dict_id," ",nline)
      special_use_flag0=special_use_flag

  char="%-11s" % code\
      +"%-55s" % expansion\

  return char,special_use_flag0,nline


def json_to_trans_024(ind,code,expansion,data_type_flag_10,f,nline):
  if nline==2:
    char=" "*11+"="*55
    nline=print_trans(f,char,"024"," ",nline)
    char=" "*11+"%-55s" % "=NOTE= Characters and digits in Column 66 are used for"
    nline=print_trans(f,char,"024"," ",nline)
    char=" "*11+"%-55s" % "       computerized checking of the field sequence"
    nline=print_trans(f,char,"024"," ",nline)
    char=" "*11+"="*55
    nline=print_trans(f,char,"024"," ",nline)
    char=" "*11+"="*55
    nline=print_trans(f,char,"024"," ",nline)
    char=" "*11+"%-55s" % "Monitor/Assumed Values"
    nline=print_trans(f,char,"024"," ",nline)
    char=" "*11+"="*55
    nline=print_trans(f,char,"024"," ",nline)
    data_type_flag_10=dict_json["024"][ind]["data_type_flag_1"]
  else:
    data_type_flag_1=dict_json["024"][ind]["data_type_flag_1"]
    if data_type_flag_1!=data_type_flag_10:
      char=" "*11+"="*55
      nline=print_trans(f,char,"024"," ",nline)
      if data_type_flag_1==2:
        char=" "*11+"%-55s" % "Quantity Measured"
      elif data_type_flag_1==3:
        char=" "*11+"%-55s" % "Resonance Parameters"
      elif data_type_flag_1==4:
        char=" "*11+"%-55s" % "Energy/Momentum of Incident Projectile"
      elif data_type_flag_1==5:
        char=" "*11+"%-55s" % "Secondary Energy"
      elif data_type_flag_1==6:
        char=" "*11+"%-55s" % "Angle"
      elif data_type_flag_1==7:
        char=" "*11+"%-55s" % "Coefficient Number"
      elif data_type_flag_1==8:
        char=" "*11+"%-55s" % "Independent Variables or Associated Inform."
      elif data_type_flag_1==9:
        char=" "*11+"%-55s" % "Isotope/Particle Identification"
      elif data_type_flag_1==0:
        char=" "*11+"%-55s" % "Additional Information"
      nline=print_trans(f,char,"024"," ",nline)

      char=" "*11+"="*55
      nline=print_trans(f,char,"024"," ",nline)
      data_type_flag_10=data_type_flag_1

  char="%-11s" % code\
      +"%-54s" % expansion\

  if dict_json["024"][ind]["family_flag"]=="*":
    char+=" " 
  else:
    char+="%1s"   % dict_json["024"][ind]["family_flag"]

  return char,data_type_flag_10,nline 


def json_to_trans_025(ind,code,expansion,sorting_flag0,f,nline):
  sorting_flag=dict_json["025"][ind]["sorting_flag"]

  if sorting_flag!=sorting_flag0:
    if sorting_flag!="DN" and sorting_flag!="DP" and sorting_flag!="ER":
      char=" "*11+"="*55
      nline=print_trans(f,char,"025"," ",nline)
      if sorting_flag=="A":
        char=" "*11+"%-55s" % "Angle"
      elif sorting_flag=="DG":
        char=" "*11+"%-55s" % "Decay"
      elif sorting_flag=="E":
        char=" "*11+"%-55s" % "Energy or inverse energy"
      elif sorting_flag=="L":
        char=" "*11+"%-55s" % "Length"
      elif sorting_flag=="T":
        char=" "*11+"%-55s" % "Time or inverse time"
      elif sorting_flag=="TEM":
        char=" "*11+"%-55s" % "Temperature"
      elif sorting_flag=="THK":
        char=" "*11+"%-55s" % "Thickness"
      elif sorting_flag=="TT":
        char=" "*11+"%-55s" % "Thick target yield"
      elif sorting_flag=="Z":
        char=" "*11+"%-55s" % "Cross section or inverse cross section"
      nline=print_trans(f,char,"025"," ",nline)

      char=" "*11+"="*55
      nline=print_trans(f,char,"025"," ",nline)
      sorting_flag0=sorting_flag

  char="%-10s" % code\
      +" "\
      +"%-33s"  % expansion\
      +"%-4s"   % dict_json["025"][ind]["unit_family_code"]\
      +" "*7\

  if dict_json["025"][ind]["conversion_factor"] is None:
    char+=" "*11
  else:
    char+="%11.4E" % dict_json["025"][ind]["conversion_factor"]

  return  char,sorting_flag0,nline


def json_to_trans_033(ind,code,expansion):
  num_eq=dict_json["033"][ind]["internal_numerical_equivalent_1"]
  if num_eq is None:
    num_eq=""
  char="%-6s"  % code\
      +" "*5\
      +"%-42s" % expansion\
      +" "*3\
      +"%6s"   % num_eq\
      +"%-1s"  % dict_json["033"][ind]["allowed_subfield_flag_1"]\
      +"%-1s"  % dict_json["033"][ind]["allowed_subfield_flag_2"]\
      +"%-1s"  % dict_json["033"][ind]["allowed_subfield_flag_3"]\
      +"%-1s"  % dict_json["033"][ind]["allowed_subfield_flag_4"]\

  return  char


def json_to_trans_034(ind,code,expansion,GENQ_flag0,f,nline):
  GENQ_flag=dict_json["034"][ind]["general_quantity_modifier_flag"]
  if GENQ_flag!=GENQ_flag0:
    if GENQ_flag=="GENQ":
      char=" "*11+"="*55
      nline=print_trans(f,char,"034"," ",nline)
      char=" "*11+"%-55s" % "The following modifiers may be added to any quantity"
      nline=print_trans(f,char,"034"," ",nline)
      char=" "*11+"%-55s" % "code without entry in Dictionary 36.  These general"
      nline=print_trans(f,char,"034"," ",nline)
      char=" "*11+"%-55s" % "quantity modifiers must be coded after any modifier"
      nline=print_trans(f,char,"034"," ",nline)
      char=" "*11+"%-55s" % "included in Dictionary 36."
      nline=print_trans(f,char,"034"," ",nline)
      char=" "*11+"="*55
      nline=print_trans(f,char,"034"," ",nline)
      GENQ_flag0=GENQ_flag

  comment_flag=" "
  comments=dict_json["034"][ind]["comment"]
  if len(comments)!=0:
    comment_flag=comments[0]["comment_flag"]

  if comment_flag=="*":
    char="%-11s" % code\
        +"%-55s" % comments[0]["comment"]
  else:
    char="%-11s" % code\
        +"%-55s" % expansion

  return char,comment_flag,GENQ_flag0,nline


def json_to_trans_045(ind,code,expansion):
  char="%-3s"  % code\
      +" "*8\
      +"%-3s"  % dict_json["045"][ind]["web_quantity_code"]\
      +" "*4\
      +"%-48s" % expansion

  return char


def json_to_trans_047(ind,code):
  char="%-11s" % code\
      +"%-10s" % dict_json["047"][ind]["cinda_reaction_code"]\
      +"%-3s"  % dict_json["047"][ind]["cinda_quantity_code"]\
      +"  "\
      +"%-1s"  % dict_json["047"][ind]["flag"]\
      +" "*39\

  return char


def json_to_trans_048(ind,code,expansion):
  char="%-5s" % code\
      +" "*6\
      +"%-10s" % dict_json["048"][ind]["short_expansion"]\
      +"%-45s" % expansion

  return char


def json_to_trans_049(ind,code):

  for item in dict_json["049"][ind]:
     if dict_json["049"][ind][item]==None:
       dict_json["049"][ind][item]=""

  char="%-8s"  % code\
      +" "*3\
      +"%-1s" % dict_json["049"][ind]["media_type"]\
      +"%-1s" % dict_json["049"][ind]["media_type_for_alternative_ISSN"]\
      +"%-1s" % dict_json["049"][ind]["doi_registerer_identifier"]\
      +"%-1s" % dict_json["049"][ind]["range_type_identifier"]\
      +" "\
      +"%-8s" % dict_json["049"][ind]["alternative_ISSN"]\
      +" "\
      +"%-6s" % dict_json["049"][ind]["reference_code_1"]\
      +"%5s" % dict_json["049"][ind]["lower_boundary_of_range_1"]\
      +"%5s" % dict_json["049"][ind]["upper_boundary_of_range_1"]\
      +"%-6s" % dict_json["049"][ind]["reference_code_2"]\
      +"%5s" % dict_json["049"][ind]["lower_boundary_of_range_2"]\
      +"%5s" % dict_json["049"][ind]["upper_boundary_of_range_2"]\
      +" "*9

  return char


def json_to_trans_144(code,expansion):
  char="%-13s" % code\
      +" "\
      +"%-52s" % expansion

  return char


def json_to_trans_213(ind,code,expansion):
  char="%-4s"  % code\
      +" "*7\
      +"%-3s"  % dict_json["213"][ind]["cinda_quantity_code"]\
      +" "*2\
      +"%-3s"  % dict_json["213"][ind]["web_quantity_code"]\
      +" "\
      +"%-46s" % expansion

  return char


def json_to_trans_227(ind,code):
  vars=code.split('-')
  if int(vars[0])<10:
    char="  "+"%-11s" % code
  elif int(vars[0])<100:
    char=" "+"%-12s" % code
  else:
    char="%-13s" % code

# if dict_json["227"][key]["a-symbol"]=="":
#   asymbol=""
# else:
#   if vars[1]=="*":
#     asymbol="%-3s" % vars[0][1:3]+vars[2]+" "
#   else:
#     asymbol="%-6s" % dict_json["227"][key]["a-symbol"]


# char+="%6s" % asymbol\
  char+="      "\
       +" "\
       +"%7s"    % dict_json["227"][ind]["internal_numerical_equivalent"]\
       +" "\
       +"%1s"    % dict_json["227"][ind]["use_flag"]\
       +" "\
       +"%-6s"   % dict_json["227"][ind]["spin_and_parity"]\
       +" "\
       +"%1s"    % dict_json["227"][ind]["state_ordering_flag"]\

  if dict_json["227"][ind]["half-life"] is None:
    char+=" "*11
  else:
    char+="%11.4E" % dict_json["227"][ind]["half-life"]\
  
  char+="%-1s" % dict_json["227"][ind]["decay_flag"]\
       +"   "

  if dict_json["227"][ind]["isotopic_abundance"] is None:
    char+=" "*13
  else:
    char+="%11.4E" % dict_json["227"][ind]["isotopic_abundance"]\
        +"  "

  return char


def json_to_trans_235(ind,code,expansion):
  char="%-1s"   % code\
      +" "*10\
      +"%-4s"   % dict_json["235"][ind]["short_expansion"]\
      +" "*2\
      +"%-35s"  % expansion\
      +" "*14

  return char


def json_to_trans_236(ind,code,expansion,reaction_type0,flag80,f,nline):
  reaction_type=dict_json["236"][ind]["reaction_type_code"]
  if reaction_type!=reaction_type0:
    if reaction_type=="CS+" or reaction_type=="CSP" or \
       reaction_type=="TT"  or reaction_type=="ALF" or \
       reaction_type=="L"   or reaction_type=="PY2" or \
       reaction_type=="DA"  or reaction_type=="DAP" or \
       reaction_type=="FC"  or reaction_type=="POF" or \
       reaction_type=="DE4" or reaction_type=="DAA" or \
       reaction_type=="D3A" or reaction_type=="FY"  or \
       reaction_type=="RP"  or reaction_type=="NQ":
      char=" "*11+"="*55
      nline=print_trans(f,char,"236"," ",nline)
      if reaction_type=="CS+":
        char=" "*11+"%-55s" % "Integral cross sections, general"
      elif reaction_type=="CSP":
        char=" "*11+"%-55s" % "Integral cross sections, partial"
      elif reaction_type=="TT":
        char=" "*11+"%-55s" % "Thick target yields"
      elif reaction_type=="ALF":
        char=" "*11+"%-55s" % "Special quantities"
      elif reaction_type=="L":
        char=" "*11+"%-55s" % "Special quantities for scattering"
      elif reaction_type=="PY2":
        char=" "*11+"%-55s" % "Product yields"
      elif reaction_type=="DA":
        char=" "*11+"%-55s" % "Angular distributions, general"
      elif reaction_type=="DAP":
        char=" "*11+"%-55s" % "Angular distributions, partial reactions"
      elif reaction_type=="FC":
        char=" "*11+"%-55s" % "Fitting coefficients"
      elif reaction_type=="POF":
        char=" "*11+"%-55s" % "Polarization of outgoing particles"
      elif reaction_type=="DE4":
        char=" "*11+"%-55s" % "Outgoing energy spectra"
      elif reaction_type=="DAA":
        char=" "*11+"%-55s" % "Double differential data"
      elif reaction_type=="D3A":
        char=" "*11+"%-55s" % "Triple differential data"
      elif reaction_type=="FY":
        char=" "*11+"%-55s" % "Fission fragment data"
      elif reaction_type=="RP":
        char=" "*11+"%-55s" % "Resonance parameters"
      elif reaction_type=="NQ":
        char=" "*11+"%-55s" % "Nuclear quantities"
      nline=print_trans(f,char,"236"," ",nline)
      char=" "*11+"="*55
      nline=print_trans(f,char,"236"," ",nline)
      reaction_type0=reaction_type

  if dict_json["236"][ind]["resonance_flag"]==".":
    ufam_resflg="%-3s" % dict_json["236"][ind]["unit_family_code"][0:3]+"."
  else:
    ufam_resflg=dict_json["236"][ind]["unit_family_code"]

  if len(expansion.rstrip())<45:
    expansion1=expansion
    expansion2=""
  else:
    chars=list(expansion)
    expansion0=""
    expansion1=""
    expansion2=""
    for i, char in enumerate(chars):
      expansion1+=char
      if len(expansion1)>44:
        expansion1=expansion0
        expansion2=expansion.replace(expansion1, "")
        break
      if char=="." or char=="," or chars[i+1]==" ":
        expansion0=expansion1

  if len(expansion2)<45:
    expansion3=""
  else:
    expansion_rest=expansion2
    chars=list(expansion_rest)
    expansion2=""
    expansion3=""
    for i, char in enumerate(chars):
      expansion2+=char
      if len(expansion2)>44:
        expansion2=expansion0
        expansion3=expansion_rest.replace(expansion2, "")
        break
      if char=="." or char=="," or chars[i+1]==" ":
        expansion0=expansion2

  if len(code)>18: # Very long quantity code
    char="%-65s" % code\
        +"9"
    nline=print_trans(f,char,"236",flag80,nline)
    char=" "*18\
        +"%-4s"  % ufam_resflg\
        +"%-44s" % expansion1

  else:
    char="%-18s" % code\
        +"%-4s"  % ufam_resflg\
        +"%-44s" % expansion1

  return char,expansion2,expansion3,reaction_type0,nline


def json_to_trans_950(code,expansion):
  char="%3s"   % int(code)\
      +" "*8\
      +"%-55s" % expansion

  return char


def get_code(dict_id,record):
  primary_key=get_primary_key(dict_id)
  code=record[primary_key]

  return code


def get_index(dict_id,code):
  primary_key=get_primary_key(dict_id)

  indexes=[dict_json[dict_id].index(x) for x in dict_json[dict_id]\
          if x[primary_key]==code]

  if len(indexes)==0:
    return -10
  else:
    return indexes[0]


def get_primary_key(dict_id):
  if dict_id=="001" or dict_id=="002" or\
     dict_id=="024" or dict_id=="025":
    primary_key="keyword"
  elif dict_id=="008":
    primary_key="atomic_number_of_element"
  elif dict_id=="950":
    primary_key="dictionary_identification_number"
  else:
    primary_key="code"

  return primary_key


def get_args(ver):

  parser=argparse.ArgumentParser(\
   usage="Convert JSONe Dictionary to TRANS Dictionary",\
   epilog="example: x4_dicj2t.py -n 9132 -i json -o dist")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-n", "--dict_ver",\
   help="dictionary version (transmission ID)")
  parser.add_argument("-i", "--dir_json",\
   help="directory of input JSON Dictionary")
  parser.add_argument("-o", "--dir_trans",\
   help="directory of output TRANS Dictionary")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("DICJ2T (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force
  dict_ver=args.dict_ver
  if dict_ver is None:
    dict_ver=input("dictionary version [9132] -------------------> ")
    if dict_ver=="":
      dict_ver="9132"
  if not re.compile(r"^9\d{3,3}$").search(dict_ver):
    print(" ** Dictionary version must be a 4-digit integer starting from 9.")
  while not re.compile(r"^\d{4,4}$").search(dict_ver):
    dict_ver=input("dictionary version [9132] -------------------> ")
    if dict_ver=="":
      dict_ver="9132"
    if not re.compile(r"^9\d{3,3}$").search(dict_ver):
      print(" ** Dictionary version must be a 4-digit integer starting from 9.")

  dir_json=args.dir_json
  if dir_json is None:
    dir_json=input("directory of input JSON Dictionary [json] ---> ")
    if dir_json=="":
      dir_json="json"
  file_in=dir_json+"/dict_"+dict_ver+".json"
  if not os.path.isfile(file_in):
    print(" ** JSON Dictionary "+file_in+" does not exist.")
  while not os.path.isfile(file_in):
    dir_json=input("directory of input JSON dictionary directory [json] ---> ")
    if dir_json=="":
      dir_json="json"
    file_in=dir_json+"/dict_"+dict_ver+".json"
    if not os.path.isfile(file_in):
      print(" ** JSON Dictionary "+file_in+" does not exist.")

  dir_trans=args.dir_trans
  if dir_trans is None:
    dir_trans=input("directory of output TRANS Dictionary [dist] -> ")
  if dir_trans=="":
    dir_trans="dist"
  if not os.path.isdir(dir_trans):
    msg="Directionry '"+dir_trans+"' does not exist and must be created."
    print_error(msg,"",force0)
    os.mkdir(dir_trans)
  file_out=dir_trans+"/trans."+dict_ver
  if os.path.isfile(file_out):
    msg="File '"+file_out+"' exists and must be overwritten."
    print_error(msg,"",force0)

  return dict_ver,dir_json,dir_trans,force0


def print_error_fatal(msg,line):
  print("** "+msg)
  print(line)
  exit()


def print_error(msg,line,force):
  print("** "+msg)
  print(line)

  if force:
    answer="Y"
  else:
    answer=""

  while answer!="Y" and answer!="N":
    answer=input("Continue? [Y] --> ")
    if answer=="":
      answer="Y"
    if answer!="Y" and answer!="N":
      print(" ** Answer must be Y (Yes) or N (No).")
  if answer=="N":
    print("program terminated")
    exit()


if __name__ == "__main__":
  dicj2t()
  exit()
