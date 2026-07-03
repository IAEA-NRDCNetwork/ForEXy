#!/usr/bin/python3
ver="2026.06.24"
############################################################
# CODUSE Ver.2026.06.24
# (Utility to analyse use of each code in Dictionary)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
############################################################
import argparse
import datetime
import glob
import json
import os
import re
import time

def coduse():
  args=get_args(ver)
  main(*get_input(args))


def main(dir_storage,file_dict,file_cinda,file_log,force0):
  time_start=time.time()

  global dict_json
  dict_json=read_dict(file_dict)

  f=open(file_log,"w")

  global code_used
  global code_used_cin
  global code_dict
  code_used=dict()
  code_used_cin=dict()
  code_dict=dict()

  dict_list=["003","004","005","006","007","015","016","017","018",\
             "019","020","021","022","023","024","025","030","033",\
             "035","037","038","144","207","209","227","236"]

  dict_list_cin=["003","004","005","006","007","030","033","047",\
                 "052","144","207","235"]

  for dict_id in dict_list:
    code_used[dict_id]=dict()
    code_dict[dict_id]=dict()
    make_code_dict(dict_id)

  for dict_id in dict_list_cin:
    code_used_cin[dict_id]=dict()
  code_cinda=read_cinda(file_cinda)

  pattern=dir_storage+"/[1-4a-z]/[1-4a-z][0-9][0-9][0-9][0-9].json"
  files=glob.glob(pattern)
  files.sort()

  for file_j4 in files:
    x4_json_full=read_json(file_j4)

    for nentry, entry in enumerate(x4_json_full["entries"]):
      an=entry["ENTRY"]["N1"]
      print("analysing ..."+an)
      x4_json=dict()
      x4_json=x4_json_full["entries"][nentry]

      for nsubent, subentry in enumerate(x4_json["subentries"]):
        if "SUBENT" in subentry:
          ansan=subentry["SUBENT"]["N1"]
          ansan=ansan[0:5]+"."+ansan[5:8]

          anal_subentry(f,ansan,subentry)

  for dict_id in dict_list:
    for code in code_dict[dict_id]:
      if code not in code_used[dict_id]:
        if dict_id in dict_list_cin:
          if code not in code_used_cin[dict_id]:
             f.write("Dict."+dict_id+": Unused in EXFOR/CINDA: "+code+"\n")
          else:
             f.write("Dict."+dict_id+": Used only in CINDA:    "+code+"\n")
        else:
          f.write("Dict."+dict_id+": Unused in EXFOR/CINDA: "+code+"\n")

  time_end=time.time()
  time_elapsed=format(time_end-time_start, ".2f")
  print("CODUSE: Processing terminated normally. "+time_elapsed+" sec.\n")  


def anal_subentry(f,ansan,subentry):

  if "INSTITUTE" in subentry:
    for element in subentry["INSTITUTE"]:
      if "coded_information" in element:
        coded_information=element["coded_information"]
        if coded_information is not None:
          for code in coded_information:
            code_anal(f,ansan,"INSTITUTE","003",code)


  if "REFERENCE" in subentry:
    for element in subentry["REFERENCE"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        for code_unit in element["coded_information"]["code_unit"]:
          field=code_unit["field"]
          anal_reference(f,ansan,"REFERENCE",field)


  if "REL-REF" in subentry:
    for element in subentry["REL-REF"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        code=coded_information["code"]
        code_anal(f,ansan,"REL-REF","017",code)
        field=coded_information["reference"]["field"]
        anal_reference(f,ansan,"REL-REF",field)


  if "REACTION" in subentry:
    for element in subentry["REACTION"]:
      if "coded_information" in element:
        coded_information=element["coded_information"]

        for code_unit in element["coded_information"]["code_unit"]:
          anal_reaction(f,ansan,"REACTION",code_unit)


  if "MONITOR" in subentry:
    for element in subentry["MONITOR"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        code=coded_information["heading"]
        if code is not None:
          code_anal(f,ansan,"MONITOR","024",code)
        for code_unit in element["coded_information"]["reaction"]["code_unit"]:
          anal_reaction(f,ansan,"MONITOR",code_unit)


  if "ASSUMED" in subentry:
    for element in subentry["ASSUMED"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        code=coded_information["heading"]
        if code is not None:
          code_anal(f,ansan,"ASSUMED","024",code)
        code=coded_information["reaction"]["code_unit"]

        for code_unit in element["coded_information"]["reaction"]["code_unit"]:
          anal_reaction(f,ansan,"ASSUMED",code_unit)


  if "RESULT" in subentry:
    for element in subentry["RESULT"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        for code in coded_information:
          code_anal(f,ansan,"RESULT","037",code)


  if "DECAY-DATA" in subentry:
    for element in subentry["DECAY-DATA"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        anal_decaydata(f,ansan,"DECAY-DATA",coded_information)


  if "DECAY-MON" in subentry:
    for element in subentry["DECAY-MON"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        if coded_information["heading"] is not None:
          code=coded_information["heading"]
          code_anal(f,ansan,"DECAY-MON","024",code)
        anal_decaydata(f,ansan,"DECAY-MON",coded_information)


  if "PART-DET" in subentry:
    for element in subentry["PART-DET"]:
      codes=element["coded_information"]
      if codes is not None:
        for code in codes:
          anal_particle(f,ansan,"PART-DET",code)


  if "RAD-DET" in subentry:
    for element in subentry["RAD-DET"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        anal_decaydata(f,ansan,"RAD-DET",coded_information)


  if "HALF-LIFE" in subentry:
    for element in subentry["HALF-LIFE"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        code=coded_information["heading"]
        code_anal(f,ansan,"HALF-LIFE","024",code)
        code=coded_information["nuclide"]
        code=re.sub(r"-L\d?$","",code)
        ind=get_index("227",code)
        if ind==-10:
          code_mod=code+"-G"
          ind=get_index("227",code_mod)
          if ind!=-10:
            code=code_mod
        code_anal(f,ansan,"HALF-LIFE","227",code)


  if "ANG-SEC" in subentry:
    for element in subentry["ANG-SEC"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        code=coded_information["heading"]
        code_anal(f,ansan,"ANG-SEC","024",code)
        code=coded_information["particle"]
        anal_particle(f,ansan,"ANG-SEC",code)

  if "EN-SEC" in subentry:
    for element in subentry["EN-SEC"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        code=coded_information["heading"]
        code_anal(f,ansan,"EN-SEC","024",code)
        code=coded_information["particle"]
        anal_particle(f,ansan,"EN-SEC",code)


  if "MOM-SEC" in subentry:
    for element in subentry["MOM-SEC"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        code=coded_information["heading"]
        code_anal(f,ansan,"MOM-SEC","024",code)
        code=coded_information["particle"]
        anal_particle(f,ansan,"MOM-SEC",code)


  if "LEVEL-PROP" in subentry:
    for element in subentry["LEVEL-PROP"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        code=coded_information["nuclide"]
        code=re.sub(r"-L\d?$","",code)
        ind=get_index("227",code)
        if ind==-10:
          code_mod=code+"-G"
          ind=get_index("227",code_mod)
          if ind!=-10:
            code=code_mod
        code_anal(f,ansan,"LEVEL-PROP","227",code)


  if "MISC-COL" in subentry:
    for element in subentry["MISC-COL"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        for code in coded_information:
          code_anal(f,ansan,"MISC-COL","024",code)


  if "MONIT-REF" in subentry:
    for element in subentry["MONIT-REF"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        code=coded_information["heading"]
        if code is not None:
          code_anal(f,ansan,"MONIT-REF","024",code)
        field=coded_information["reference"]["field"]
        anal_reference(f,ansan,"REL-REF",field)


  if "FACILITY" in subentry:
    for element in subentry["FACILITY"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        for code in coded_information["facility"]:
          code_anal(f,ansan,"FACILITY","018",code)
        if coded_information["institute"] is not None:
          code=coded_information["institute"]
          code_anal(f,ansan,"FACILITY","003",code)


  if "INC-SOURCE" in subentry:
    for element in subentry["INC-SOURCE"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        codes=coded_information["incident_source"]
        if codes is not None:
          for code in codes:
            code_anal(f,ansan,"INC-SOURCE","019",code)
        code=coded_information["reaction"]
        if code is not None:
          anal_reaction(f,ansan,"INC-SOURCE",code)



  if "INC-SPECT" in subentry:
    for element in subentry["INC-SPECT"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        for code in coded_information:
          code_anal(f,ansan,"INC-SPECT","024",code)


  if "SAMPLE" in subentry:
    for element in subentry["SAMPLE"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        code=coded_information["nuclide"]
        if code is not None:  
          ind=get_index("227",code)
          if ind==-10:
            code_mod=code+"-G"
            ind=get_index("227",code_mod)
            if ind!=-10:
              code=code_mod
          code_anal(f,ansan,"SAMPLE","227",code)


  if "DETECTOR" in subentry:
    for element in subentry["DETECTOR"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        for code in coded_information:
          code_anal(f,ansan,"DETECTOR","022",code)


  if "METHOD" in subentry:
    for element in subentry["METHOD"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        for code in coded_information:
          code_anal(f,ansan,"METHOD","021",code)


  if "ANALYSIS" in subentry:
    for element in subentry["ANALYSIS"]:
      if "coded_information" in element:
        coded_information=element["coded_information"]
        if coded_information is not None:
          for code in coded_information:
            code_anal(f,ansan,"ANALYSIS","023",code)


  if "ERR-ANALYS" in subentry:
    for element in subentry["ERR-ANALYS"]:
      if "coded_information" in element:
        coded_information=element["coded_information"]
        if coded_information is not None:
          code=coded_information["heading"]
          code_anal(f,ansan,"ERR-ANALYS","024",code)


  if "ADD-RES" in subentry:
    for element in subentry["ADD-RES"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        for code in coded_information:
          code_anal(f,ansan,"ADD-RES","020",code)


  if "SUPPL-INF" in subentry:
    for element in subentry["SUPPL-INF"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        for code in coded_information:
          code_anal(f,ansan,"SUPPL-INF","038",code)


  if "STATUS" in subentry:
    for element in subentry["STATUS"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        codes=coded_information["status"]
        for code in codes:
          code_anal(f,ansan,"STATUS","016",code)
        if coded_information["reference"] is not None:
          field=coded_information["reference"]["field"]
          if field is not None:
            anal_reference(f,ansan,"STATUS",field)
 
 
  if "HISTORY" in subentry:
    for element in subentry["HISTORY"]:
      coded_information=element["coded_information"]
      if coded_information is not None:
        code=coded_information["history"]
        if code is not None:
          code_anal(f,ansan,"HISTORY","015",code)


  if "COMMON" in subentry:
    codes=subentry["COMMON"]["heading"]
    for code in codes:
      code_anal(f,ansan,"COMMON","024",code)
    codes=subentry["COMMON"]["unit"]
    for code in codes:
      code_anal(f,ansan,"COMMON","025",code)


  if "DATA" in subentry:
    codes=subentry["DATA"]["heading"]
    for code in codes:
      code_anal(f,ansan,"DATA","024",code)
    codes=subentry["DATA"]["unit"]
    for code in codes:
      code_anal(f,ansan,"DATA","025",code)


def anal_reaction(f,ansan,keyword,code_unit):
  code=code_unit["field"]["target"]
  code=re.sub(r"-L\d?$","",code)
  ind=get_index("209",code)
  if ind!=-10:
    code_anal(f,ansan,keyword,"209",code)
  else:
    ind=get_index("227",code)
    if ind==-10:
      code_mod=code+"-G"
      ind=get_index("227",code_mod)
      if ind!=-10:
        code=code_mod
    code_anal(f,ansan,keyword,"227",code)

  code=code_unit["field"]["projectile"]
  if re.compile(r"^\d+\-[A-Z]+\-\d+").search(code):
    code=re.sub(r"-L\d?$","",code)
    ind=get_index("227",code)
    if ind==-10:
      code_mod=code+"-G"
      ind=get_index("227",code_mod)
      if ind!=-10:
        code=code_mod
    code_anal(f,ansan,keyword,"227",code)
  else:
    code_anal(f,ansan,keyword,"033",code)

  process=code_unit["field"]["process"]
  codes=process.split("+")
  for code in codes:
    if re.compile(r"^\d+\-[A-Z]+\-\d+").search(code):
      code_anal(f,ansan,keyword,"227",code)
    elif code!="0":
      ind=get_index("030",code)
      if ind==-10:
        code=re.sub(r"^\d+","",code)
        code_anal(f,ansan,keyword,"033",code)
      else:
        code_anal(f,ansan,keyword,"030",code)

  code=code_unit["field"]["product"]
  if code!="" and code!="ELEM" and code!="MASS" and\
     code!="ELEM/MASS" and code!="NPART":
    ind=get_index("209",code)
    if ind!=-10:
      code_anal(f,ansan,keyword,"209",code)
    else:
      nucls=[]
      arr=code.split("-")
      if len(arr)==3:
        nucls.append(code)
      elif len(arr)==4:
        base=arr[0]+"-"+arr[1]+"-"+arr[2]
        isoflags=re.split(r"\+|\/",arr[3])
        for isoflag in isoflags:
          if isoflag=="T":
            nucl=base
          else:
            nucl=base+"-"+isoflag
          nucls.append(nucl)
     
      if len(nucls)>0:
        for nucl in nucls:
          nucl=re.sub(r"-L\d?$","",nucl)
          ind=get_index("227",nucl)
          if ind==-10:
            nucl_mod=nucl+"-G"
            ind=get_index("227",nucl_mod)
            if ind!=-10:
              nucl=nucl_mod
            else:
              nucl_mod=re.sub(r"-G$","",nucl)
              ind=get_index("227",nucl_mod)
              if ind!=-10:
                nucl=nucl_mod
          code_anal(f,ansan,keyword,"227",nucl)

  if keyword!="INC-SOURCE":
    code=code_unit["field"]["data_type"]
    if code is not None:
      code_anal(f,ansan,keyword,"035",code)
   
    code=code_unit["field"]["quantity"]
    sfs=code.split(',')
    if len(sfs)>2:
      sf7=sfs[2]
      if sf7!="":
        codes=re.split(r'\+|\/',sf7)
        for code in codes: 
          ind=get_index("030",code)
          if ind==-10:
            code_anal(f,ansan,keyword,"033",code)
          else:
            code_anal(f,ansan,keyword,"030",code)
    

    code=code_unit["field"]["quantity_236"]
    if code is None:
      code=code_unit["field"]["quantity"]
    code_anal(f,ansan,keyword,"236",code)

  return


def anal_reference(f,ansan,keyword,field):
  type=field["reference_type"]
  code_anal(f,ansan,keyword,"004",type)
  code=field["reference"]["code"]
  if type=="J" or type=="K":
    code_anal(f,ansan,keyword,"005",code)
  elif type=="P" or type=="R" or type=="S":
    ind=get_index("006",code)
    if ind==-10:
      code_mod=code.rstrip("-")
      ind=get_index("006",code_mod)
      if ind!=-10:
        code=code_mod
    code_anal(f,ansan,keyword,"006",code)
  elif type=="A" or type=="C":
    code_anal(f,ansan,keyword,"007",code)
  elif type=="3":
    code_anal(f,ansan,keyword,"144",code)
  elif type=="B":
    code_anal(f,ansan,keyword,"207",code)

  return


def anal_decaydata(f,ansan,keyword,coded_information):
   code=coded_information["nuclide"]
   code=re.sub(r"-L\d?$","",code)
   ind=get_index("227",code)
   if ind==-10:
     code_mod=code+"-G"
     ind=get_index("227",code_mod)
     if ind!=-10:
       code=code_mod
   code_anal(f,ansan,keyword,"227",code)

   if keyword!="RAD-DET":
     if coded_information["half-life"] is not None:
       code=coded_information["half-life"]["unit"]
       code_anal(f,ansan,keyword,"025",code)

   if "radiation" in coded_information:
     if keyword=="RAD-DET":
       codes=coded_information["radiation_type"]
       for code in codes:
         code_anal(f,ansan,keyword,"033",radiation)
     else:
       radiations=coded_information["radiation"]
       for radiation in radiations:
         codes=radiation["radiation_type"]
         for code in codes:
           code_anal(f,ansan,keyword,"033",code)

   return


def anal_particle(f,ansan,keyword,code):
  if code=="B+":
    codes=["B+"]
  else:
    codes=re.split(r"\+|/",code)
  for code in codes:
    if re.compile(r"^\d+\-[A-Z]+\-\d+").search(code):
      code=re.sub(r"-L\d?$","",code)
      ind=get_index("227",code)
      if ind==-10:
        code_mod=code+"-G"
        ind=get_index("227",code_mod)
        if ind!=-10:
          code=code_mod
      code_anal(f,ansan,keyword,"227",code)
    else:
      code_anal(f,ansan,keyword,"033",code)

  return


def read_json(file):
  f=open(file)
  try:
    j=json.load(f)
  except json.JSONDecodeError:
    msg=file+" is not in JSON format."
    print(msg)
    exit() 

  f.close()
  return j


def get_file_lines(file):
  if os.path.exists(file):
    f=open(file, "r")
    lines=f.readlines()
    f.close()
  else:
    msg="File "+file+" does not exist."
    print_error_fatal(msg)
  return lines


def read_dict(file_dict):
  f=open(file_dict)
  try:
    dict_json=json.load(f)
  except json.JSONDecodeError:
    msg=file_dict+" is not in JSON format."
    print_error_fatal(msg,"")

  if dict_json["title"]!="EXFOR/CINDA Dictionary in JSON":
    msg=file_dict+" is not an EXFOR/CINDA Dictionary in JSON."
    print_error_fatal(msg,"")

  return dict_json


def read_cinda(file_cinda):
  lines=get_file_lines(file_cinda)
  for line in lines:
    if re.compile(r"^\#").search(line):
      continue
    elif re.compile(r"^(\d\d\d):(.+?)\s+$").search(line):
      m=re.compile(r"^(\d\d\d):(.+?)\s+$").search(line)
      dict_id=m.group(1) 
      code=m.group(2)
      code_used_cin[dict_id][code]=1
    else:
      msg=file_cinda+" does not follow the expected format."
      print_error_fatal(msg,line)

  return


def make_code_dict(dict_id):
  primary_key=get_primary_key(dict_id)
  for element in dict_json[dict_id]:
    code=element[primary_key]
    code_dict[dict_id][code]=1
  return


def get_index(dict_id,code):
  if code=="":
    return -10

  primary_key=get_primary_key(dict_id)

  indexes=[dict_json[dict_id].index(x) for x in dict_json[dict_id]\
          if x[primary_key]==code]

  if len(indexes)==0:
    return -10
  elif len(indexes)>1:
    msg="Code '"+code+"' is defined twice in Dictionary "+dict_id+"?"
    print_error_fatal(msg,"")
  else:
    index=indexes[0]
    return index


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


def code_anal(f,ansan,keyword,dict_id,code):
  ind=get_index(dict_id,code)
  if ind==-10:
    keywordout="%-10s" % keyword
    f.write(ansan+": "+keywordout+": Undefined in Dict."+dict_id+": "+code+"\n")
  else:
    status=dict_json[dict_id][ind]["status_code"]
    if status!="OBS" and status!="EXT" and status!="TRA":
      keywordout="%-10s" % keyword
      f.write(ansan+": "+keywordout+": Code with unexpected status '"+status+"' in Dict."+dict_id+": "+code+"\n")
    else:
      code_used[dict_id][code]=1

  return


def print_error_fatal(msg,line):
  print("**  "+msg)
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


def get_args(ver):
  parser=argparse.ArgumentParser(\
   usage="Analysis of code usage in J4 files",\
   epilog="example: x4_coduse.py -i j4 -d dict.json -c x4_coduse.cin")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-i", "--dir_storage",\
   help="directory of input J4 storage")
  parser.add_argument("-d", "--file_dict",\
   help="input JSON dictionary")
  parser.add_argument("-c", "--file_cinda",\
   help="input JSON dictionary")
  parser.add_argument("-l", "--file_log",\
   help="output log file (optional)", default="x4_coduse.log")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("CODUSE (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force

  dir_storage=args.dir_storage
  if dir_storage is None:
    dir_storage=input("directory of input J4 storage [j4] ----> ")
    if dir_storage=="":
      dir_storage="j4"

  if not os.path.isdir(dir_storage):
    print(" ** Directory '"+dir_storage+"' does not exist.")
  while not os.path.isdir(dir_storage):
    dir_storage=input("directory of input J4 storage [j4] ----> ")
    if dir_storage=="":
      dir_storage="entry"
    if not os.path.isdir(dir_storage):
      print(" ** Directory '"+dir_storage+"' does not exist.")

  file_dict=args.file_dict
  if file_dict is None:
    file_dict=input("input JSON Dictionary [dict.json] -----> ")
    if file_dict=="":
      file_dict="dict.json"
  if not os.path.exists(file_dict):
    print(" ** File "+file_dict+" does not exist.")
  while not os.path.exists(file_dict):
    file_dict=input("input JSON Dictionary [dict.json] -----> ")
    if file_dict=="":
      file_dict="dict.json"
    if not os.path.exists(file_dict):
      print(" ** File "+file_dict+" does not exist.")

  file_cinda=args.file_cinda
  if file_cinda is None:
    file_cinda=input("input CINDA code list [x4_coduse.cin] -> ")
    if file_cinda=="":
      file_cinda="x4_coduse.cin"
  if not os.path.exists(file_cinda):
    print(" ** File "+file_cinda+" does not exist.")
  while not os.path.exists(file_cinda):
    file_cinda=input("input CINDA code list [x4_coduse.cin] -> ")
    if file_cinda=="":
      file_cinda="x4_coduse.cin"
    if not os.path.exists(file_cinda):
      print(" ** File "+file_cinda+" does not exist.")

  file_log=args.file_log
  print("output log file -----------------------> "+file_log)
  print("\n")
  if os.path.isfile(file_log):
    msg="File '"+file_log+"' exists and must be overwritten."
    print_error(msg,"",force0)

  return dir_storage,file_dict,file_cinda,file_log,force0


if __name__ == "__main__":
  coduse()
  exit()
