#!/usr/bin/python3
ver="2026.06.24"
###########################################################
# DICA2J Ver.2026.06.24
# (Converter from Archive Dictionary to JSON Dictionary)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
###########################################################
import argparse
import datetime
import json
import os
import re
import time
from datetime import timezone

def dica2j():
  args=get_args(ver)
  main(*get_input(args))


def main(dict_ver,dir_archive,dir_json,force0):
  time_start=time.time()

  global country_list
  global organization_list
  global dict_json
  force=force0

  organization_list=dict()
  country_list=dict()

  dictionary_list=[
  "001",  "002", "003", "004", "005", "006", "007", "008",
  "015",  "016", "017", "018", "019",
  "020",  "021", "022", "023", "024", "025", "026",
  "030",  "031", "032", "033", "034", "035", "037", "038",
  "043",  "045", "047", "048", "049", 
  "052", 
  "113",  "144",
  "207",  "209", "213", "227", "235", "236"]

# 026 and 113 must be loaded before their printing 
#  since presence of the unit family is checked for
#  Dict.024 and 025 and presence of the web quantity
#  checked for Dict.045.
#

  dictionary_list_add=["026a", "113a"]
  dictionary_list=dictionary_list_add+dictionary_list

  dict_in_use_list=["026", "045", "113", "213"]

  time_now=datetime.datetime.now(timezone.utc)
  time_out=time_now.strftime("%Y-%m-%dT%H:%M:%S%z")

  dict_json=dict()
  dict_json={
   "title"          : "EXFOR/CINDA Dictionary in JSON",
   "transmission_id": dict_ver,
   "time_stamp"     : time_out
  }


# Read Archive Dictionary to Python dictionary
  for dict_id in dictionary_list:
    dict_id=dict_id.replace("a","")
    dict_json[dict_id]=archive_to_json(dir_archive,dict_id)
    if dict_id=="025":
      del dict_json["026"]
    elif dict_id=="045":
      del dict_json["113"]
  dict_json["950"]=archive_to_json_950(dir_archive)


# Check if code is uniquely defined
  for dict_id in dictionary_list:
    primary_key=get_primary_key(dict_id)
    codes=dict()
    if dict_id in dictionary_list_add:
      continue
    for record in dict_json[dict_id]:
      code=record[primary_key] 
      if code in codes:
        msg="Code "+code+" defined twice in Dictionary "+dict_id
        print_error_3(dict_id,code,msg)


# Check dependency (unit family and web quantity)
  for dict_in_use in dict_in_use_list:
    for record in dict_json[dict_in_use]:
      primary_key=get_primary_key(dict_in_use)
      code=record[primary_key]
      check_dict_use(dict_in_use,code)


# Produce JSON Dictionary
  json_out=json.dumps(dict_json,indent=2)
  print("printing json dictionary    ... ")
  file_out=dir_json+"/dict_"+dict_ver+".json"
  f=open(file_out,'w')
  f.write(json_out)
  f.close()

  time_end=time.time()
  time_elapsed=format(time_end-time_start, ".2f")
  print("DICA2J: Processing terminated normally. "+time_elapsed+" sec.\n")


def get_args(ver):

  parser=argparse.ArgumentParser(\
   usage="Convert Archive Dictionaries to JSON Dictionary",\
   epilog="example: x4_dica2j.py -n 9132 -i input -o json")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-n", "--dict_ver",\
   help="dictionary version (transmission ID)")
  parser.add_argument("-i", "--dir_archive",\
   help="directory of input Archive Dictionaries")
  parser.add_argument("-o", "--dir_json",\
   help="directory of output JSON Dictionary")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("DICA2J (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force

  dict_ver=args.dict_ver
  if dict_ver is None:
    dict_ver=input("dictionary version [9132] -----------------------> ")
    if dict_ver=="":
      dict_ver="9132"
  if not re.compile(r"^9\d{3,3}$").search(dict_ver):
    print(" ** Dictionary version must be a 4-digit integer starting from 9.")
  while not re.compile(r"^\d{4,4}$").search(dict_ver):
    dict_ver=input("input dictionary version [9132] -----------------------> ")
    if dict_ver=="":
      dict_ver="9132"
    if not re.compile(r"^9\d{3,3}$").search(dict_ver):
      print(" ** Dictionary version must be a 4-digit integer starting from 9.")

  dir_archive=args.dir_archive
  if dir_archive is None:
    dir_archive=input("directory of input Archive Dictionaries [input] -> ")
    if dir_archive=="":
      dir_archive="input"
  if not os.path.exists(dir_archive):
    print(" ** Directory "+dir_archive+" does not exist.")
  while not os.path.exists(dir_archive):
    dir_archive=input("directory of input Archive Dictionaries [input] -> ")
    if dir_archive=="":
      dir_archive="input"
    if not os.path.exists(dir_archive):
      print(" ** Directory "+dir_archive+" does not exist.")

  dir_json=args.dir_json
  if dir_json is None:
    dir_json=input("directory of output JSON Dictionary [json] ------> ")
  if dir_json=="":
    dir_json="json"
  if not os.path.isdir(dir_json):
    msg="Directionry '"+dir_json+"' does not exist and must be created."
    print_error(msg,"",force0)
    os.mkdir(dir_json)
  file_out=dir_json+"/dict_"+dict_ver+".json"
  if os.path.isfile(file_out):
    msg="File '"+file_out+"' exists and must be overwritten."
    print_error(msg,"",force0)

  return dict_ver,dir_archive,dir_json,force0


def read_archive(dict_id,line):
  alteration_flag_list=[" ","A","D","M","S"]
  status_code_list=["CIN","DEL","EXT","INT","OBS","PRE","PRO","TRA"]

  alteration_flag=line[0:1]
  status_code=line[1:4]
  date=line[5:11]
  key=line[12:41]
  key=key.rstrip()
  key=key.lstrip()

  if alteration_flag not in alteration_flag_list:
    msg="Unknown alteration flag."
    print_error_2(dict_id,key,msg,line,0,1)

  if status_code not in status_code_list:
    msg="Unknown status code."
    print_error_2(dict_id,key,msg,line,0,1)

  if not re.compile(r"\S+").search(key): # COMMENT record
    return alteration_flag,status_code,date,key

  if not re.compile(r"\d{6,6}").search(date):
    msg="Illegal date."
    print_error_2(dict_id,key,msg,line,5,11)

  year=date[0:2]
  if year!="19" and year!="20":
    msg="Illegal year."
    print_error_2(dict_id,key,msg,line,5,9)

  month=date[4:6]
  if not re.compile(r"^(0[1-9]|1[0-2])$").search(month):
    msg="Illegal month."
    print_error_2(dict_id,key,msg,line,9,11)

  return alteration_flag,status_code,date,key


def str2int(dict_id,key,line,col1,col2):
  char=line[col1:col2]
  if re.compile(r"^\s*$").search(char):
    char=None
  else:
    try:
      int(char)
    except ValueError:
      msg="Integer expected but illegal characters found"
      print_error_2(dict_id,key,msg,line,col1,col2)
      char="?"
    else:
      char=int(char)
  return char


def str2float(dict_id,key,line,col1,col2):
  char=line[col1:col2]
  if re.compile(r"^\s*$").search(char):
    char=None
  else:
    char=re.sub(r"\s+","",char)
    char=re.sub(r"(\d|\.)(-|\+)","\\1E\\2",char)
    try:
      float(char)
    except ValueError:
      msg="Real number expected but illegal characters found"
      print_error_2(dict_id,key,msg,line,col1,col2)
      char="?"
    else:
      char=float(char)
  return char


def get_comment(dict_id,key,line):
  if not re.compile(r"\S").search(line[43:123]):
    msg="Blank comment record"
    print_error_2(dict_id,key,msg,line,43,123)

    flag=None
    text=None

  else:
    if re.compile(r"\S").search(line[4:43]):
      msg="Comment wrongly placed"
      print_error_2(dict_id,key,msg,line,4,43)

    if dict_id=="002" or dict_id=="227":
      flag=None
      text=None
      if re.compile(r"\S").search(line[43:123]):
        msg="Comment not allowed"
        print_error_2(dict_id,key,msg,line,43,123)

    elif dict_id=="003" or dict_id=="006":
      flag_list=["=", " "]
      flag=line[43:44]
      if flag not in flag_list:
        msg="Col.44 of comment record must be = or blank"
        print_error_2(dict_id,key,msg,line,43,44)

      text=line[44:98].rstrip()
      if re.compile(r"\S").search(line[98:123]):
        msg="Comment wrongly placed"
        print_error_2(dict_id,key,msg,line,98,123)

    elif dict_id=="005":
      flag_list=["+", "*", ".", "=", " "]
      flag=line[43:44]
      if flag not in flag_list:
        msg="Col.44 of comment record must be +, *, ., = or blank"
        print_error_2(dict_id,key,msg,line,43,44)

      text=line[44:99].rstrip()
      if re.compile(r"\S").search(line[99:123]):
        msg="Comment wrongly placed"
        print_error_2(dict_id,key,msg,line,99,123)

    elif dict_id=="007" or dict_id=="207":
      flag_list=["(", "=", " "]
      flag=line[43:44]
      if flag not in flag_list:
        msg="Col.44 of comment record must be (, = or blank"
        print_error_2(dict_id,key,msg,line,43,44)

      text=line[44:98].rstrip()
      if re.compile(r"\S").search(line[98:123]):
        msg="Comment wrongly placed"
        print_error_2(dict_id,key,msg,line,98,123)

    elif dict_id=="016":
      flag_list=["R", "S"," "]
      flag=line[103:104]

      text=line[43:98].rstrip()
      if key=="comment":
        if not re.compile(r"^\s{5}(R|S)\s{19}$").search(line[98:123]):
          msg="Comment wrongly placed"
          print_error_2(dict_id,key,msg,line,98,123)
      elif re.compile(r"\S").search(line[98:123]):
        msg="Comment wrongly placed"
        print_error_2(dict_id,key,msg,line,98,123)


    elif dict_id=="033" or dict_id=="209":
      flag=None

      text=line[45:100].rstrip()
      if line[43:45]!="  ":
        msg="Col.44-45 of comment record must blank"
        print_error_2(dict_id,key,msg,line,43,45)
      if re.compile(r"\S").search(line[100:123]):
        msg="Comment wrongly placed"
        print_error_2(dict_id,key,msg,line,100,123)

    elif dict_id=="034":
      flag_list=["*", " "]
      flag=line[43:44]
      if flag not in flag_list:
        msg="Col.44 of comment record must be * or blank"
        print_error_2(dict_id,key,msg,line,43,44)

      text=line[44:99].rstrip()
      if re.compile(r"\S").search(line[99:123]):
        msg="Comment wrongly placed"
        print_error_2(dict_id,key,msg,line,99,123)


    elif dict_id=="213":
      flag=None

      text=line[65:111].rstrip()
      if re.compile(r"\S").search(line[0:65]):
        msg="Comment wrongly placed"
        print_error_2(dict_id,key,msg,line,0,65)
      elif re.compile(r"\S").search(line[111:123]):
        msg="Comment wrongly placed"
        print_error_2(dict_id,key,msg,line,111,123)


    elif dict_id=="236":
      flag=None

      text=line[43:123].rstrip()
      if re.compile(r"\S").search(line[87:123]):
        msg="Comment wrongly placed"
        print_error_2(dict_id,key,msg,line,87,123)

    else:
      flag=None

      text=line[43:98].rstrip()
      if re.compile(r"\S").search(line[98:123]):
        msg="Comment wrongly placed"
        print_error_2(dict_id,key,msg,line,98,123)

  return flag,text


def get_long_expansion(dict_id,key,long_exp,long_exp_flag,col,line):
  if re.compile(r"\S").search(line[4:43]):
    msg="Long expansion wrongly placed"
    print_error_2(dict_id,key,msg,line,4,43)

  if re.compile(r"\S").search(line[col:123]):
    msg="Long expansion wrongly placed"
    print_error_2(dict_id,key,msg,line,col,123)

  chars=line[43:col].rstrip()

  for i, char in enumerate(chars):
    if i==0 and long_exp!="": # head of continuing line
      long_exp+=" "
    if long_exp_flag>0 or long_exp=="":
      long_exp+=char
      if char=="(":
        long_exp_flag+=1
      elif char==")":
        long_exp_flag-=1
    elif char!=" ":
      msg="Extra character after end of long expansion"
      col=43+i
      print_error_2(dict_id,key,msg,line,col,123)
      break

  long_exp=long_exp.replace("  "," ")
  return long_exp,long_exp_flag


def check_master_record_length(dict_id,key,line):
  lenmax={"001": 108, "002":  75, "003": 118, "004":  85, "005": 123,
          "006":  99, "007": 114, "008":  98, "015":  95, "016": 104,
          "017":  96, "018": 100, "019": 101, "020":  96, "021": 100,
          "022": 100, "023": 100, "024": 122, "025":  96, "026":  99,
          "030": 112, "031": 112, "032": 112, "033": 111, "034": 117,
          "035":  93, "037":  96, "038":  96, "043":  83, "045":  98,
          "047":  59, "048":  98, "049": 121, "052": 118, "113":  98,
          "144": 103, "207": 114, "209": 114, "213": 111, "227": 122,
          "235":  84, "236": 123}
  if len(line.rstrip())>lenmax[dict_id]:
    msg="Master record exceeds maximum length ("+str(lenmax[dict_id])+")"
    print_error_2(dict_id,key,msg,line,lenmax[dict_id],123)

  return


def archive_to_json(dir_archive,dict_id):
  dictionary=[]
  key0=""

  file_in=dir_archive+"/dict_arc_new."+dict_id
  lines=get_file_lines(file_in)
  for line in lines:
    (alteration_flag,status_code,date,key)=read_archive(dict_id,line)
    if len(line)!=123:
      msg="Line length must be 123."
      col1=min(123,len(line))
      col2=max(123,len(line))
      if key=="":
        print_error_2(dict_id,key0,msg,line,col1,col2)
      else:
        print_error_2(dict_id,key,msg,line,col1,col2)

    if re.compile(r"\S+").search(key): # Master record
      check_master_record_length(dict_id,key,line)
      check_void_master(dict_id,key,line)
      alteration_flag0=alteration_flag
      status_code0=status_code
      key0=key
      long_exp_flag=-1
      if dict_id=="001":
        dictionary.append(archive_to_json_001(key,line))
      elif dict_id=="002":
        dictionary.append(archive_to_json_002(key,line))
      elif dict_id=="003":
        dictionary.append(archive_to_json_003(key,line))
      elif dict_id=="004":
        dictionary.append(archive_to_json_004(key,line))
      elif dict_id=="005":
        dictionary.append(archive_to_json_005(key,line))
      elif dict_id=="006":
        dictionary.append(archive_to_json_006(key,line))
      elif dict_id=="007":
        dictionary.append(archive_to_json_007(key,line))
      elif dict_id=="008":
        dictionary.append(archive_to_json_008(key,line))
      elif dict_id=="015":
        dictionary.append(archive_to_json_015(key,line))
      elif dict_id=="016":
        dictionary.append(archive_to_json_016(key,line))
      elif dict_id=="017":
        dictionary.append(archive_to_json_017(key,line))
      elif dict_id=="018":
        dictionary.append(archive_to_json_018(key,line))
      elif dict_id=="019":
        dictionary.append(archive_to_json_019(key,line))
      elif dict_id=="020":
        dictionary.append(archive_to_json_020(key,line))
      elif dict_id=="021":
        dictionary.append(archive_to_json_021(key,line))
      elif dict_id=="022":
        dictionary.append(archive_to_json_022(key,line))
      elif dict_id=="023":
        dictionary.append(archive_to_json_023(key,line))
      elif dict_id=="024":
        dictionary.append(archive_to_json_024(key,line))
      elif dict_id=="025":
        dictionary.append(archive_to_json_025(key,line))
      elif dict_id=="026":
        dictionary.append(archive_to_json_026(key,line))
      elif dict_id=="030":
        dictionary.append(archive_to_json_030(key,line))
      elif dict_id=="031":
        dictionary.append(archive_to_json_031(key,line))
      elif dict_id=="032":
        dictionary.append(archive_to_json_032(key,line))
      elif dict_id=="033":
        dictionary.append(archive_to_json_033(key,line))
      elif dict_id=="034":
        dictionary.append(archive_to_json_034(key,line))
      elif dict_id=="035":
        dictionary.append(archive_to_json_035(key,line))
      elif dict_id=="037":
        dictionary.append(archive_to_json_037(key,line))
      elif dict_id=="038":
        dictionary.append(archive_to_json_038(key,line))
      elif dict_id=="043":
        dictionary.append(archive_to_json_043(key,line))
      elif dict_id=="045":
        dictionary.append(archive_to_json_045(key,line))
      elif dict_id=="047":
        dictionary.append(archive_to_json_047(key,line))
      elif dict_id=="048":
        dictionary.append(archive_to_json_048(key,line))
      elif dict_id=="049":
        dictionary.append(archive_to_json_049(key,line))
      elif dict_id=="052":
        dictionary.append(archive_to_json_052(key,line))
      elif dict_id=="113":
        dictionary.append(archive_to_json_113(key,line))
      elif dict_id=="144":
        dictionary.append(archive_to_json_144(key,line))
      elif dict_id=="207":
        dictionary.append(archive_to_json_207(key,line))
      elif dict_id=="209":
        dictionary.append(archive_to_json_209(key,line))
      elif dict_id=="213":
        dictionary.append(archive_to_json_213(key,line))
      elif dict_id=="227":
        dictionary.append(archive_to_json_227(key,line))
      elif dict_id=="235":
        dictionary.append(archive_to_json_235(key,line))
      elif dict_id=="236":
        dictionary.append(archive_to_json_236(key,line))

      dictionary[-1]["alteration_flag"]=alteration_flag
      dictionary[-1]["status_code"]=status_code
      dictionary[-1]["date"]=date

    elif key0=="":  # COMMENT record at the top of the dictionary
      key0="comment"
      alteration_flag0=alteration_flag
      long_exp_flag=0
      status_code0=status_code
      (flag,text)=get_comment(dict_id,key0,line)
      primary_key=get_primary_key(dict_id)
      if flag is None:
        dictionary.append({primary_key:"","comment":[text],"status_code":status_code})
      else:
        dictionary.append({primary_key:"","comment":[{"comment_flag":flag,"comment":text}],"status_code":status_code})

    else: # other COMMENT records including long expansion field

      if alteration_flag!=alteration_flag0:
        msg="Alteration flag "+alteration_flag0+" is expected but "\
           +alteration_flag+" is given in the commend record"
        print_error_2(dict_id,key0,msg,line,0,1)
      
      if status_code!=status_code0:
        msg="Status code "+status_code0+" is expected but "\
           +status_code+" is given in the comment record"
        print_error_2(dict_id,key0,msg,line,1,4)

      if dict_id=="005" or dict_id=="007" or dict_id=="207" or dict_id=="236":
        if dict_id=="005" or dict_id=="007" or dict_id=="207":
          col=98
        elif dict_id=="236":
          col=87
        if long_exp_flag==-1 and line[43:44]=="(":# 1st line of lon.exp.
          (long_exp,long_exp_flag)=\
           get_long_expansion(dict_id,key0,"",0,col,line)
          if long_exp_flag==0:                  # lon.exp. closed
            long_exp=re.sub(r"^\(|\)$","",long_exp)
            dictionary[-1]["long_expansion"]=long_exp
        elif long_exp_flag>0:                     # con.line of lon.exp.
          (long_exp,long_exp_flag)=\
           get_long_expansion(dict_id,key0,long_exp,long_exp_flag,col,line)
          if long_exp_flag==0:                  # lon.exp. closed
            long_exp=re.sub(r"^\(|\)$","",long_exp)
            dictionary[-1]["long_expansion"]=long_exp
        else:
          (flag,text)=get_comment(dict_id,key0,line)
          if flag is None:
            dictionary[-1]["comment"].append(text)
          else:
            flag_text={"comment_flag":flag,"comment":text}
            dictionary[-1]["comment"].append(flag_text)

      else:
        (flag,text)=get_comment(dict_id,key0,line)
        if flag is None:
          dictionary[-1]["comment"].append(text)
        else:
          flag_text={"comment_flag":flag,"comment":text}
          dictionary[-1]["comment"].append(flag_text)

  return dictionary


def get_numerical_equivalent(dict_id,key,line,col1,col2):
  num_eq=str2int(dict_id,key,line,col1,col2)

#Uniqueness checking of numerical equivalent within dictionary
#if num_eq in num_eq_list[dict_id]:
#  msg="Internal numerical equivalent not unique" 
#  print_error_2(dict_id,key,msg,line,col1,col2)
#elif num_eq!=None:
#  num_eq_list[dict_id].append(num_eq)

  return num_eq

def get_area_country(dict_id,key,extra_area,line,col):
  area_code_list=["1","2","3","4"]

  area1=str2int(dict_id,key,line,col,col+1)
  if str(area1) not in area_code_list:
    msg="Unknown area code"
    print_error_2(dict_id,key,msg,line,col,col+1)

  country1=line[col+1:col+4].rstrip()
  area2=line[col+4:col+5].strip()
  country2=line[col+5:col+8].rstrip()
  
  if country1=="ZZZ":
    if area2!="":
      msg="Country code is ZZZ but additional area code is not blank"
      print_error_2(dict_id,key,msg,line,col+1,col+5)

    organization_code=str(area1)+"ZZZ"+country2
    if organization_code not in [d.get('code') for d in dict_json["003"]]:
      msg="Unknown international organization code"
      print_error_2(dict_id,key,msg,line,col,col+8)
  elif country1 not in country_list:
    msg="Unknown country code"
    print_error_2(dict_id,key,msg,line,col+1,col+4)
  
  if area2=="":
    if country1!="ZZZ" and country2!="": 
      msg="Additional area code is blank but country code is not ZZZ"
      print_error_2(dict_id,key,msg,line,col+1,col+5)
  else:
    if area2 not in area_code_list and area2!=extra_area:
      msg="Unknown additional area code"
      print_error_2(dict_id,key,msg,line,col+4,col+5)
    if country2 not in country_list:
      msg="Unknown additional country code"
      print_error_2(dict_id,key,msg,line,col+5,col+8)
    elif area2!=extra_area and area2!=str(country_list[country2]):
      msg="Illegal combination of additional area and country code"
      print_error_2(dict_id,key,msg,line,col+4,col+8)

  return area1,country1,area2,country2


def get_expansion(dict_id,key,type,line,col1,col2):
  expansion=line[col1:col2].rstrip()
  if expansion=="":
    if type==" ":
      msg="Expansion absent"
    elif type=="S":
      msg="Short expansion absent"
    elif type=="L":
      msg="Long expansion absent"
    else:
      msg="Expansion (type unknown) absent"
    print_error_2(dict_id,key,msg,line,col1,col2)
  return expansion


def get_unit_family_code(dict_id,key,line,col1,col2):
  unit_family_code=line[col1:col2].rstrip()
  if unit_family_code!="":
    if unit_family_code not in [d.get('code') for d in dict_json["026"]]:
      msg="Unknown unit family flag"
      print_error_2(dict_id,key,msg,line,col1,col2)
    else:
      dict_id_int=str(re.sub("^0","", dict_id))
      dictionary_use=\
      [d.get('dictionary_'+dict_id_int+'_use') for d in dict_json["026"] if d["code"]==unit_family_code][0]
      dict_id_int=int(re.sub("236","36",dict_id_int))
      if dictionary_use!=dict_id_int:
        msg="Unit family flag not allowed in Dict."+dict_id
        print_error_2(dict_id,key,msg,line,col1,col2)

  return unit_family_code


def get_reference_code(dict_id,key,line,col1,col2):
  reference_code=line[col1:col2].rstrip()
  if reference_code!="":
    if reference_code not in [d.get('code') for d in dict_json["005"]]:
      msg="Unknown reference code"
      print_error_2(dict_id,key,msg,line,col1,col2)

  return reference_code


def get_web_quantity_code(dict_id,key,line,col1,col2):
  web_quantity_code=line[col1:col2].rstrip()
  if web_quantity_code!="":
    if web_quantity_code not in [d.get('code') for d in dict_json["113"]]:
      msg="Unknown web quantity code"
      print_error_2(dict_id,key,msg,line,col1,col2)

  return web_quantity_code


def get_cinda_quantity_code(dict_id,key,line,col1,col2):
  cinda_quantity_code=line[col1:col2].rstrip()
  if cinda_quantity_code!="":
    if cinda_quantity_code not in [d.get('code') for d in dict_json["045"]]:
      msg="Unknown CINDA quantity code"
      print_error_2(dict_id,key,msg,line,col1,col2)

  return cinda_quantity_code


def get_reaction_type_code(dict_id,key,line,col1,col2):
  reaction_type_code=line[col1:col2].rstrip()
  if reaction_type_code!="":
    if reaction_type_code not in [d.get('code') for d in dict_json["213"]]:
      msg="Unknown reaction type code"
      print_error_2(dict_id,key,msg,line,col1,col2)

  return reaction_type_code


def archive_to_json_001(key,line):

  num_eq=get_numerical_equivalent("001",key,line,43,52)
  expansion=get_expansion("001",key," ",line,53,108)

  dictionary_entry=dict()
  dictionary_entry={
    "keyword"                            :key,
    "internal_numerical_equivalent"      :num_eq,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_002(key,line):
  dictionary_entry=dict()
  key_required_list=["R", "B", "X"]
  code_required_list=["R", "O"]

  expansion=get_expansion("002",key," ",line,43,68)
  key_required=line[68:69].strip()
  num_eq=get_numerical_equivalent("002",key,line,69,71)
  code_required=line[71:72].strip()
  pointer=str2int("002",key,line,72,75)

  if key_required!="" and key_required not in key_required_list:
    msg="Unknown keyword required code"
    print_error_2("002","",msg,line,68,69)

  if code_required!="" and code_required not in code_required_list:
    msg="Unknown code required code"
    print_error_2("002","",msg,line,71,72)

  dictionary_entry={
    "keyword"                            :key,
    "expansion"                          :expansion,
    "keyword_required"                   :key_required,
    "internal_numerical_equivalent"      :num_eq,
    "code_required"                      :code_required,
    "pointer_to_related_dictionary"      :pointer,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_003(key,line):
  area_code_list=[1,2,3,4]

  cinda_code=line[43:46].rstrip()
  area_code=str2int("003",key,line,46,47)
  country_code=line[47:50].rstrip()
  expansion=get_expansion("002",key," ",line,50,103)
  country_for_cinda=line[103:118].rstrip()

  if cinda_code!=key[4:]:
    msg="CINDA code inconsistent with the institute code"
    print_error_2("003","",msg,line,43,46)
  
  if area_code not in area_code_list:
    msg="Unknown area code"
    print_error_2("003","",msg,line,46,47)
  
  if country_code=="ZZZ":
    organization_list[cinda_code]=area_code
  elif cinda_code==country_code:
    country_list[country_code]=area_code
  if len(country_code)==2:
    country_code+=" "
  if country_code!=key[1:4]:
    msg="Country code inconsistent with the institute code"
    print_error_2("003",key,msg,line,47,50)

      
  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "cinda_code"                         :cinda_code,
    "area_code"                          :area_code,
    "country_code"                       :country_code,
    "expansion"                          :expansion,
    "country_for_cinda"                  :country_for_cinda,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_004(key,line):

  short_expansion=get_expansion("004",key,"S",line,43,47)
  pointer=str2int("004",key,line,47,50)
  expansion=get_expansion("004",key," ",line,50,85)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "short_expansion"                    :short_expansion,
    "pointer_to_related_dictionary"      :pointer,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_005(key,line):

  cinda_code=line[43:47].rstrip()
  (area1,country1,area2,country2)=get_area_country("005",key,"T",line,47)
  short_expansion=get_expansion("005",key,"S",line,55,75)
  expansion=get_expansion("005",key," ",line,75,123)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "cinda_code"                         :cinda_code,
    "area_code"                          :area1,
    "country_code"                       :country1,
    "additional_area_code"               :area2,
    "additional_country_code"            :country2,
    "short_expansion"                    :short_expansion,
    "expansion"                          :expansion,
    "long_expansion"                     :"",
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_006(key,line):
  cinda_flag_list=["*"]

  institute_code=line[43:50].rstrip()
  expansion=get_expansion("006",key," ",line,50,98)
  cinda_flag=line[98:99].strip()

  if institute_code not in [d.get('code') for d in dict_json["003"]]:
    msg="Unknown institute code"
    print_error_2("006","",msg,line,43,50)

  if cinda_flag!="":
    if cinda_flag not in cinda_flag_list:
      msg="Unknown CINDA flag"
      print_error_2("006","",msg,line,98,99)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "institute_code"                     :institute_code,
    "expansion"                          :expansion,
    "cinda_flag"                         :cinda_flag,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_007(key,line):

  expansion=get_expansion("007",key," ",line,43,96)
  (area1,country1,area2,country2)=get_area_country("007",key,"T",line,96)
  cinda_short_code=line[104:114].rstrip()

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "expansion"                          :expansion,
    "area_code"                          :area1,
    "country_code"                       :country1,
    "additional_area_code"               :area2,
    "additional_country_code"            :country2,
    "cinda_short_code"                   :cinda_short_code,
    "long_expansion"                     :"",
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_008(key,line):

  element_symbol=line[43:45].rstrip()
  element_name=line[45:65].rstrip()

  dictionary_entry=dict()
  dictionary_entry={
    "atomic_number_of_element"           :key,
    "element_symbol"                     :element_symbol,
    "element_name"                       :element_name,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_015(key,line):

  short_expansion=get_expansion("015",key,"S",line,43,58)
  expansion=get_expansion("015",key," ",line,58,95)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "short_expansion"                    :short_expansion,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_016(key,line):
  san_field_flag_list=["R", "S"]

  num_eq=get_numerical_equivalent("016",key,line,43,48)
  expansion=get_expansion("016",key," ",line,48,100)
  san_field_flag=line[103:104].strip()

  if san_field_flag!="":
    if san_field_flag not in san_field_flag_list:
      msg="Unknown subetry number field flag"
      print_error_2("016",key,msg,line,103,104)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "internal_numerical_equivalent"      :num_eq,
    "expansion"                          :expansion,
    "subentry_number_field_flag"         :san_field_flag,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_017(key,line):

  expansion=get_expansion("017",key," ",line,43,96)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_018(key,line):
  special_use_flag_list=["NEUT", "PHOT"]

  expansion=get_expansion("018",key," ",line,43,96)
  special_use_flag=line[96:100].rstrip()

  if special_use_flag!="":
    if special_use_flag not in special_use_flag_list:
      msg="Unknown special use flag"
      print_error_2("018",key,msg,line,96,100)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "expansion"                          :expansion,
    "special_use_flag"                   :special_use_flag,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_019(key,line):
  special_use_flag_list=["NEUT", "PHOT"]
  delimiter_flag_list=["=", ","]

  expansion=get_expansion("019",key," ",line,43,96)
  special_use_flag=line[96:100].rstrip()
  delimiter_flag=line[100:101].rstrip()

  if special_use_flag!="":
    if special_use_flag not in special_use_flag_list:
      msg="Unknown special use flag"
      print_error_2("019",key,msg,line,96,100)

  if delimiter_flag!="":
    if delimiter_flag not in delimiter_flag_list:
      msg="Unknown delimiter flag"
      print_error_2("019",key,msg,line,100,101)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "expansion"                          :expansion,
    "special_use_flag"                   :special_use_flag,
    "delimiter_flag"                     :delimiter_flag,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_020(key,line):
  expansion=get_expansion("020",key," ",line,43,96)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_021(key,line):
  special_use_flag_list=["FY", "NEUT"]

  expansion=get_expansion("021",key," ",line,43,96)
  special_use_flag=line[96:100].rstrip()

  if special_use_flag!="":
    if special_use_flag not in special_use_flag_list:
      msg="Unknown special use flag"
      print_error_2("021",key,msg,line,96,100)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "expansion"                          :expansion,
    "special_use_flag"                   :special_use_flag,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_022(key,line):
  special_use_flag_list=["NEU", "GAM"]

  expansion=get_expansion("022",key," ",line,43,96)
  special_use_flag=line[96:100].rstrip()

  if special_use_flag!="":
    if special_use_flag not in special_use_flag_list:
      msg="Unknown special use flag"
      print_error_2("022",key,msg,line,96,100)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "expansion"                          :expansion,
    "special_use_flag"                   :special_use_flag,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_023(key,line):
  special_use_flag_list=["RP", "PHOT"]

  expansion=get_expansion("023",key," ",line,43,96)
  special_use_flag=line[96:100].rstrip()

  if special_use_flag!="":
    if special_use_flag not in special_use_flag_list:
      msg="Unknown special use flag"
      print_error_2("023",key,msg,line,96,100)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "expansion"                          :expansion,
    "special_use_flag"                   :special_use_flag,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_024(key,line):
  data_type_flag_list=[
    "01", "02", "03", "09",
    "1None",
    "11", "15",
    "21", "22",
    "31", "32",
    "41", "42", "43", "44", "45",
    "51", "52", "53", "54", "55", "56", "57", "58", "59",
    "61", "62", "63", "68",
    "75", "78",
    "82", "83", "84", "85", "86", "87",
    "91", "92", "93", "94", "95", "98", "99"]

  family_flag_list=[" ",
                    "A", "B", "C", "D", "E", "F", "G", "H", "I",
                    "J", "P", "Q", "S", "L", "M", "R", "N",
                    "*",
                    "K", "Z", "8", "9", "6", "7", "4", "2", "0"]

  plotting_flag_list=[
    "000",
    "100", "110", "120", "200", "210", "220",
    "300", "310", "320", "400", "410", "420",
    "910", "901", "911", "920", "902", "922", 
    "930", "903", "933", "940", "904", "944", 
    "950", "905", "955"]

  special_use_flag_list=["RHI"]

  data_type_flag_1=str2int("024",key,line,43,44)
  data_type_flag_2=str2int("024",key,line,44,45)
  family_flag=line[45:46]
  plotting_flag_1=str2int("024",key,line,46,47)
  plotting_flag_2=str2int("024",key,line,47,48)
  plotting_flag_3=str2int("024",key,line,48,49)
  plotting_flag_4=str2int("024",key,line,49,50)
  plotting_flag_5=str2int("024",key,line,50,51)
  plotting_flag_6=str2int("024",key,line,51,52)
  plotting_flag_7=str2int("024",key,line,52,53)
  unit_family_code=get_unit_family_code("024",key,line,53,57)
  expansion=get_expansion("024",key," ",line,58,112)
  special_use_flag=line[118:122].rstrip()

  data_type_flag=str(data_type_flag_1)+str(data_type_flag_2)
  if data_type_flag not in data_type_flag_list:
    msg="Unknown combination of data type flag 1 and 2"
    print_error_2("024",key,msg,line,43,45)

  if family_flag not in family_flag_list:
    msg="Unknown family flag"
    print_error_2("024",key,msg,line,45,46)

  plotting_flag=str(plotting_flag_1)+str(plotting_flag_2)+str(plotting_flag_3)
  if plotting_flag not in plotting_flag_list:
    msg="Unknown combination of plotting flag 1 to 3"
    print_error_2("024",key,msg,line,46,49)

  plotting_flag=str(plotting_flag_4)+str(plotting_flag_5)+str(plotting_flag_6)
  if plotting_flag not in plotting_flag_list:
    msg="Unknown combination of plotting flag 4 to 6"
    print_error_2("024",key,msg,line,49,52)

  if plotting_flag_7!=0 and plotting_flag_7!=1:
    msg="Unknown plotting flag 7"
    print_error_2("024",key,msg,line,52,53)

  if special_use_flag!="":
    if special_use_flag not in special_use_flag_list:
      msg="Unknown special use flag"
      print_error_2("024",key,msg,line,118,122)

  dictionary_entry=dict()
  dictionary_entry={
    "keyword"                            :key,
    "data_type_flag_1"                   :data_type_flag_1,
    "data_type_flag_2"                   :data_type_flag_2,
    "family_flag"                        :family_flag,
    "plotting_flag_1"                    :plotting_flag_1,
    "plotting_flag_2"                    :plotting_flag_2,
    "plotting_flag_3"                    :plotting_flag_3,
    "plotting_flag_4"                    :plotting_flag_4,
    "plotting_flag_5"                    :plotting_flag_5,
    "plotting_flag_6"                    :plotting_flag_6,
    "plotting_flag_7"                    :plotting_flag_7,
    "unit_family_code"                   :unit_family_code,
    "expansion"                          :expansion,
    "special_use_flag"                   :special_use_flag,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_025(key,line):

  expansion=get_expansion("025",key," ",line,43,76)
  unit_family_code=get_unit_family_code("025",key,line,78,82)
  conversion_factor=str2float("025",key,line,82,93)
# conversion_factor=line[82:93].strip()
  sorting_flag=line[93:96].rstrip()

  dictionary_entry=dict()
  dictionary_entry={
    "keyword"                            :key,
    "expansion"                          :expansion,
    "unit_family_code"                   :unit_family_code,
    "conversion_factor"                  :conversion_factor,
    "sorting_flag"                       :sorting_flag,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_026(key,line):

  dictionary_24_use=str2int("026",key,line,43,45)
  dictionary_25_use=str2int("026",key,line,45,47)
  dictionary_236_use=str2int("026",key,line,47,49)
  expansion=get_expansion("025",key," ",line,49,99)

  if dictionary_24_use!=24 and dictionary_24_use!=None:
    msg="Unexpected Dictionary 24 flag"
    print_error_2("026",key,msg,line,43,45)
  
  if dictionary_25_use!=25 and dictionary_25_use!=None:
    msg="Unexpected Dictionary 25 flag"
    print_error_2("026",key,msg,line,45,47)
  
  if dictionary_236_use!=36 and dictionary_236_use!=None:
    msg="Unexpected Dictionary 236 flag"
    print_error_2("026",key,msg,line,47,49)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "dictionary_24_use"                  :dictionary_24_use,
    "dictionary_25_use"                  :dictionary_25_use,
    "dictionary_236_use"                 :dictionary_236_use,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_030(key,line):
  special_use_flag_list=["PHOT"]

  num_eq=get_numerical_equivalent("030",key,line,43,53)
  expansion=get_expansion("030",key," ",line,53,108)
  special_use_flag=line[108:112].rstrip()

  if special_use_flag!="":
    if special_use_flag not in special_use_flag_list:
      msg="Unknown special use flag"
      print_error_2("030",key,msg,line,108,112)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "internal_numerical_equivalent"      :num_eq,
    "expansion"                          :expansion,
    "special_use_flag"                   :special_use_flag,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_031(key,line):
  special_use_flag_list=["PHOT", "RHID"]

  num_eq=get_numerical_equivalent("031",key,line,43,53)
  expansion=get_expansion("031",key," ",line,53,108)
  special_use_flag=line[108:112].rstrip()

  if special_use_flag!="":
    if special_use_flag not in special_use_flag_list:
      msg="Unknown special use flag"
      print_error_2("031",key,msg,line,108,112)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "internal_numerical_equivalent"      :num_eq,
    "expansion"                          :expansion,
    "special_use_flag"                   :special_use_flag,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_032(key,line):
  special_use_flag_list=["RHID"]

  num_eq=get_numerical_equivalent("032",key,line,43,53)
  expansion=get_expansion("031",key," ",line,53,108)
  special_use_flag=line[108:112].rstrip()

  if special_use_flag!="":
    if special_use_flag not in special_use_flag_list:
      msg="Unknown special use flag"
      print_error_2("032",key,msg,line,108,112)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "internal_numerical_equivalent"      :num_eq,
    "expansion"                          :expansion,
    "special_use_flag"                   :special_use_flag,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_033(key,line):

# Num.Eq.1 is not an integer for neutron and neutral pion
# num_eq_1=get_numerical_equivalent("0331",key,line,43,49)
# num_eq_2=get_numerical_equivalent("0332",key,line,49,54)

  num_eq_1=line[43:49].strip()
  num_eq_2=line[49:54].strip()
  allowed_subfield_flag_1=line[54:55].rstrip()
  allowed_subfield_flag_2=line[55:56].rstrip()
  allowed_subfield_flag_3=line[56:57].rstrip()
  allowed_subfield_flag_4=line[57:58].rstrip()
  expansion=get_expansion("033",key," ",line,58,98)
  nuclide_code=line[98:111].rstrip()

  if allowed_subfield_flag_1!="D" and allowed_subfield_flag_1!="":
    msg="Unknown allowed sub field flag 1"
    print_error_2("032",key,msg,line,54,55)
  if allowed_subfield_flag_2!="2" and allowed_subfield_flag_2!="":
    msg="Unknown allowed sub field flag 2"
    print_error_2("032",key,msg,line,55,56)
  if allowed_subfield_flag_3!="3" and allowed_subfield_flag_3!="":
    msg="Unknown allowed sub field flag 3"
    print_error_2("032",key,msg,line,56,57)
  if allowed_subfield_flag_4!="7" and allowed_subfield_flag_4!="":
    msg="Unknown allowed sub field flag 4"
    print_error_2("032",key,msg,line,57,58)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "internal_numerical_equivalent_1"    :num_eq_1,
    "internal_numerical_equivalent_2"    :num_eq_2,
    "allowed_subfield_flag_1"            :allowed_subfield_flag_1,
    "allowed_subfield_flag_2"            :allowed_subfield_flag_2,
    "allowed_subfield_flag_3"            :allowed_subfield_flag_3,
    "allowed_subfield_flag_4"            :allowed_subfield_flag_4,
    "expansion"                          :expansion,
    "nuclide_code"                       :nuclide_code,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_034(key,line):
  genq_flag_list=["GENQ", "GENQA", "GENQM", "GENQN", "GENQP"]
  special_use_flag_list=["RHID"]

  num_eq=get_numerical_equivalent("034",key,line,43,53)
  genq_flag=line[53:58].rstrip()
  expansion=get_expansion("034",key," ",line,58,113)
  special_use_flag=line[113:117].rstrip()

  if genq_flag!="":
    if genq_flag not in genq_flag_list:
      msg="Unknown general quantity modifier flag"
      print_error_2("034",key,msg,line,53,58)
  
  if special_use_flag!="":
    if special_use_flag not in special_use_flag_list:
      msg="Unknown special use flag"
      print_error_2("034",key,msg,line,113,117)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "internal_numerical_equivalent"      :num_eq,
    "general_quantity_modifier_flag"     :genq_flag,
    "expansion"                          :expansion,
    "special_use_flag"                   :special_use_flag,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_035(key,line):
  num_eq=get_numerical_equivalent("035",key,line,43,53)
  expansion=get_expansion("035",key," ",line,53,93)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "internal_numerical_equivalent"      :num_eq,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_037(key,line):
  expansion=get_expansion("037",key," ",line,43,96)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_038(key,line):
  expansion=get_expansion("038",key," ",line,43,96)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_043(key,line):
  expansion=get_expansion("043",key," ",line,43,83)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_045(key,line):
  web_quantity_code=get_web_quantity_code("045",key,line,43,46)
  expansion=get_expansion("045",key," ",line,50,98)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "web_quantity_code"                  :web_quantity_code,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_047(key,line):
  flag_list=["*"]

  cinda_reaction_code=line[43:53].rstrip()
  cinda_quantity_code=get_cinda_quantity_code("047",key,line,53,56)

  flag=line[58:59].rstrip()
  if flag!="":
    if flag not in flag_list:
      msg="Unknown flag"
      print_error_2("047",key,msg,line,58,59)
       
  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "cinda_reaction_code"                :cinda_reaction_code,
    "cinda_quantity_code"                :cinda_quantity_code,
    "flag"                               :flag,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_048(key,line):
  short_expansion=get_expansion("048",key,"S",line,43,53)
  expansion=get_expansion("048",key," ",line,53,98)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "short_expansion"                    :short_expansion,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_049(key,line):

  media_type=line[43:44]
  media_type_for_alternative_ISSN=line[44:45].rstrip()
  doi_registerer_identifier=line[45:46]
  range_type_identifier=line[46:47]
  alternative_ISSN=line[48:56].rstrip()
  reference_code_1=get_reference_code("049",key,line,57,63)
  lower_boundary_of_range_1=str2int("049",key,line,63,68)
  upper_boundary_of_range_1=str2int("049",key,line,68,73)
  reference_code_2=get_reference_code("049",key,line,73,79)
  lower_boundary_of_range_2=str2int("049",key,line,79,84)
  upper_boundary_of_range_2=str2int("049",key,line,84,89)
  reference_code_3=get_reference_code("049",key,line,89,95)
  lower_boundary_of_range_3=str2int("049",key,line,95,100)
  upper_boundary_of_range_3=str2int("049",key,line,100,105)
  reference_code_4=get_reference_code("049",key,line,105,111)
  lower_boundary_of_range_4=str2int("049",key,line,111,116)
  upper_boundary_of_range_4=str2int("049",key,line,116,121)

  if media_type!="P" and media_type!="E":
    msg="Unknown media type" 
    print_error_2("049",key,msg,line,43,44)
  if media_type_for_alternative_ISSN!="E" and\
     media_type_for_alternative_ISSN!="S" and\
     media_type_for_alternative_ISSN!="":
    msg="Unknown media type for alternative ISSN" 
    print_error_2("049",key,msg,line,44,45)
  if doi_registerer_identifier!="1":
    msg="Unknown DOI registerer identifier" 
    print_error_2("049",key,msg,line,45,46)
  if range_type_identifier!="V" and range_type_identifier!="Y":
    msg="Unknown range type identifier" 
    print_error_2("049",key,msg,line,46,47)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "media_type"                         :media_type,
    "media_type_for_alternative_ISSN"    :media_type_for_alternative_ISSN,
    "doi_registerer_identifier"          :doi_registerer_identifier,
    "range_type_identifier"              :range_type_identifier,
    "alternative_ISSN"                   :alternative_ISSN,                   
    "reference_code_1"                   :reference_code_1,                   
    "lower_boundary_of_range_1"          :lower_boundary_of_range_1,          
    "upper_boundary_of_range_1"          :upper_boundary_of_range_1,          
    "reference_code_2"                   :reference_code_2,                   
    "lower_boundary_of_range_2"          :lower_boundary_of_range_2,          
    "upper_boundary_of_range_2"          :upper_boundary_of_range_2,          
    "reference_code_3"                   :reference_code_3,                   
    "lower_boundary_of_range_3"          :lower_boundary_of_range_3,          
    "upper_boundary_of_range_3"          :upper_boundary_of_range_3,          
    "reference_code_4"                   :reference_code_4,                   
    "lower_boundary_of_range_4"          :lower_boundary_of_range_4,          
    "upper_boundary_of_range_4"          :upper_boundary_of_range_4,          
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_052(key,line):
  expansion=get_expansion("052",key," ",line,43,98)
  country=line[103:118].rstrip()

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "expansion"                          :expansion,
    "country"                            :country,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_113(key,line):
  expansion=get_expansion("113",key," ",line,43,98)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_144(key,line):
  (area1,country1,area2,country2)=get_area_country("144",key,"",line,43)
  expansion=get_expansion("144",key," ",line,51,103)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "area_code"                          :area1,
    "country_code"                       :country1,
    "additional_area_code"               :area2,
    "additional_country_code"            :country2,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_207(key,line):

  expansion=get_expansion("207",key," ",line,43,96)
  (area1,country1,area2,country2)=get_area_country("207",key,"T",line,96)
  cinda_short_code=line[104:114].rstrip()

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "expansion"                          :expansion,
    "area_code"                          :area1,
    "country_code"                       :country1,
    "additional_area_code"               :area2,
    "additional_country_code"            :country2,
    "cinda_short_code"                   :cinda_short_code,
    "long_expansion"                     :"",
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_209(key,line):

  cinda_code=line[43:48].rstrip()
  num_eq_1=get_numerical_equivalent("209",key,line,48,55)
  num_eq_2=get_numerical_equivalent("209",key,line,55,62)
  expansion=get_expansion("209",key," ",line,83,108)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "cinda_code"                         :cinda_code,
    "internal_numerical_equivalent_1"    :num_eq_1,
    "internal_numerical_equivalent_2"    :num_eq_2,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_213(key,line):

  cinda_quantity_code=get_cinda_quantity_code("213",key,line,43,46)
  web_quantity_code=get_web_quantity_code("213",key,line,48,51)
  sorting_flag=str2int("213",key,line,52,54)
  ind_var_fam_flag_1=str2int("213",key,line,55,56)
  ind_var_fam_flag_3=str2int("213",key,line,57,58)
  ind_var_fam_flag_4=str2int("213",key,line,58,59)
  ind_var_fam_flag_5=str2int("213",key,line,59,60)
  ind_var_fam_flag_6=str2int("213",key,line,60,61)
  ind_var_fam_flag_7=str2int("213",key,line,61,62)
  expansion=get_expansion("213",key," ",line,65,111)

  if ind_var_fam_flag_1!=1 and ind_var_fam_flag_1!=None:
    msg="Unknown independent variable family flag 1"
    print_error_2("213",key,msg,line,55,56)

  if ind_var_fam_flag_3!=3 and ind_var_fam_flag_3!=None:
    msg="Unknown independent variable family flag 3"
    print_error_2("213",key,msg,line,57,58)

  if ind_var_fam_flag_4!=4 and ind_var_fam_flag_4!=None:
    msg="Unknown independent variable family flag 4"
    print_error_2("213",key,msg,line,58,59)

  if ind_var_fam_flag_5!=5 and ind_var_fam_flag_5!=None:
    msg="Unknown independent variable family flag 5"
    print_error_2("213",key,msg,line,59,60)

  if ind_var_fam_flag_6!=6 and ind_var_fam_flag_6!=None:
    msg="Unknown independent variable family flag 6"
    print_error_2("213",key,msg,line,60,61)

  if ind_var_fam_flag_7!=7 and ind_var_fam_flag_7!=None:
    msg="Unknown independent variable family flag 7"
    print_error_2("213",key,msg,line,61,62)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "cinda_quantity_code"                :cinda_quantity_code,
    "web_quantity_code"                  :web_quantity_code,
    "sorting_flag"                       :sorting_flag,
    "independent_variable_family_flag_1" :ind_var_fam_flag_1,
    "independent_variable_family_flag_3" :ind_var_fam_flag_3,
    "independent_variable_family_flag_4" :ind_var_fam_flag_4,
    "independent_variable_family_flag_5" :ind_var_fam_flag_5,
    "independent_variable_family_flag_6" :ind_var_fam_flag_6,
    "independent_variable_family_flag_7" :ind_var_fam_flag_7,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_227(key,line):
  num_eq=get_numerical_equivalent("227",key,line,49,56)

  use_flag=line[56:57]
  if use_flag!=" " and use_flag!="Z":
    msg="Unknown use flag"
    print_error_2("227",key,msg,line,56,57)

# if re.compile(r"\d").search(line[57:63]):
#   spin_and_parity=str2float("227",key,line,57,63)
#   spin_and_parity=line[57:63]
# else:
#   spin_and_parity=None

  state_ordering_flag=line[63:64]
  if state_ordering_flag!=" " and state_ordering_flag!="*":
    msg="Unknown state ordering flag"
    print_error_2("227",key,msg,line,63,64)

  if re.compile(r"\d").search(line[64:75]):
    half_life=str2float("227",key,line,64,75)
  else:
    half_life=None

  decay_flag=line[75:76]
  if decay_flag!=" " and decay_flag!="S"\
 and decay_flag!="U" and decay_flag!="P":
    msg="Unknown decay flag"
    print_error_2("227",key,msg,line,75,76)

  mass_flag=line[76:77]
  if mass_flag!=" " and mass_flag!="#":
    msg="Unknown mass flag"
    print_error_2("227",key,msg,line,76,77)

  energy_flag=line[77:78]
  if energy_flag!=" " and energy_flag!="#":
    msg="Unknown energy flag"
    print_error_2("227",key,msg,line,77,78)

  if re.compile(r"\d").search(line[78:89]):
    isotopic_abundance=str2float("227",key,line,78,89)
  else:
    isotopic_abundance=None

  if re.compile(r"\d").search(line[89:101]):
    atomic_weight=str2float("227",key,line,89,101)
  else:
    atomic_weight=None

  if re.compile(r"\d").search(line[101:113]):
    excitation_energy=str2float("227",key,line,101,113)
  else:
    excitation_energy=None

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "internal_numerical_equivalent"      :num_eq,
    "use_flag"                           :use_flag,
    "spin_and_parity"                    :line[57:63].rstrip(),
    "state_ordering_flag"                :state_ordering_flag,
    "half-life"                          :half_life,
    "decay_flag"                         :decay_flag,
    "mass_flag"                          :mass_flag,
    "energy_flag"                        :energy_flag,
    "isotopic_abundance"                 :isotopic_abundance,
    "atomic_weight"                      :atomic_weight,
    "excitation_energy"                  :excitation_energy,
    "explanation"                        :line[113:122].rstrip(),
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_235(key,line):
  short_expansion=get_expansion("235",key,"S",line,43,47)
  expansion=get_expansion("235",key," ",line,49,84)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "short_expansion"                    :short_expansion,
    "expansion"                          :expansion,
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_236(key,line):
  resonance_flag_list=["."]

  reaction_type_code=get_reaction_type_code("236",key,line,43,47)
  unit_family_code=get_unit_family_code("236",key,line,47,51)
  resonance_flag=line[51:52].rstrip()
  expansion=get_expansion("236",key," ",line,52,123)

  if resonance_flag!="":
    if resonance_flag not in resonance_flag_list:
      msg="Unknown resonance flag"
      print_error_2("236",key,msg,line,51,52)

  dictionary_entry=dict()
  dictionary_entry={
    "code"                               :key,
    "reaction_type_code"                 :reaction_type_code,
    "unit_family_code"                   :unit_family_code,
    "resonance_flag"                     :resonance_flag,
    "expansion"                          :expansion,
    "long_expansion"                     :"",
    "comment"                            :[]}

  return dictionary_entry


def archive_to_json_950(dir_archive):
  dictionary=[]
  file_in=dir_archive+"/dict_arc.top"
  lines=get_file_lines(file_in)
  for line in lines:
    key=line[0:3].lstrip().zfill(3)
    if len(line)!=123:
      msg="Line length must be 123."
      col1=min(123,len(line))
      col2=max(123,len(line))
      print_error_2("950",key,msg,line,col1,col2)
    number_of_daniel_keys=str2int("950",key,line,35,37)

    dictionary_entry=dict()
    dictionary_entry={
      "dictionary_identification_number"   :key,
      "dictionary_name"                    :line[4:34].rstrip(),
      "number_of_daniel_keys"              :number_of_daniel_keys,
      "formats_of_key_and_expansion_fields":line[38:82].rstrip()
    }
    dictionary.append(dictionary_entry)

  return dictionary


def check_dict_use(dict_id,code):
  key_rel_list={"026": "unit_family_code",
                "045": "cinda_quantity_code",
                "113": "web_quantity_code",
                "213": "reaction_type_code"}
  dict_id_rel_list={"026": ["024", "025", "236"],
                    "045": ["047", "213"],
                    "113": ["045", "213"],
                    "213": ["236"]}
  key_name={"026": "Unit family code",
            "045": "CINDA quantity code",
            "113": "Web quantity code",
            "213": "Reaction type code"}

  found=False
  use024=None
  use025=None
  use236=None

  for dict_id_rel in dict_id_rel_list[dict_id]:
    for ind, record_rel in enumerate(dict_json[dict_id_rel]):
      code_rel=get_code(dict_id_rel, record_rel)
      if code_rel=="": # comment
        continue
      if dict_json[dict_id_rel][ind][key_rel_list[dict_id]]==code:
        found=True
        if dict_id=="026":
          if dict_id_rel=="024":
            use024=24
          elif dict_id_rel=="025":
            use025=25
          elif dict_id_rel=="236":
            use236=36

  if not found:
    msg=key_name[dict_id]+" not in use"
    print_error_3(dict_id,code,msg)

  if dict_id=="026":
    ind=get_index("026",code)

    if use024 is None and\
       dict_json["026"][ind]["dictionary_24_use"]==24:
      msg=code+" has flag=24 but not in use in Dict.24"
      print_error_3("026",code,msg) 
    elif use024=="024" and\
         dict_json["026"][ind]["dictionary_24_use"] is None:
      msg=code+" does not have flag=24 but in use in Dict.24"
      print_error_3("026",code,msg) 

    if use025 is None and\
       dict_json["026"][ind]["dictionary_25_use"]==25:
      msg=code+" has flag=25 but not in use in Dict.25"
      print_error_3("026",code,msg) 
    elif use025=="025" and\
         dict_json["026"][ind]["dictionary_25_use"] is None:
      msg=code+" does not have flag=25 but in use in Dict.25"
      print_error_3("026",code,msg) 

    if use236 is None and\
       dict_json["026"][ind]["dictionary_236_use"]==36:
      msg=code+" has flag=36 but not in use in Dict.236"
      print_error_3("026",code,msg) 
    elif use236=="236" and\
         dict_json["026"][ind]["dictionary_236_use"] is None:
      msg=code+" does not have flag=36 but in use in Dict.236"
      print_error_3("026",code,msg) 


  return


def check_void_master(dict_id,key,line):
  void_list_ini={"001": [23,53,109],
                 "002": [23,76],
                 "003": [20,119],
                 "004": [14,86],
                 "005": [19],
                 "006": [24,100],
                 "007": [23,115],
                 "008": [16,66],
                 "015": [14,96],
                 "016": [18,101,105],
                 "017": [14,97],
                 "018": [18,101],
                 "019": [18,102],
                 "020": [18,97],
                 "021": [18,101],
                 "022": [18,101],
                 "023": [18,101],
                 "024": [23,58,113,123],
                 "025": [23,77,97],
                 "026": [17,100],
                 "030": [16,113],
                 "031": [18,113],
                 "032": [16,113],
                 "033": [19,112],
                 "034": [18,118],
                 "035": [18,94],
                 "037": [18,97],
                 "038": [18,97],
                 "043": [15,84],
                 "045": [16,47,99],
                 "047": [16,57,60],
                 "048": [18,99],
                 "049": [48,57,122],
                 "052": [15,99,119],
                 "113": [16,99],
                 "144": [26,104],
                 "207": [23,115],
                 "209": [23,63,109,115],
                 "213": [17,47,55,57,63,112],
                 "227": [26],
                 "235": [14,48,85],
                 "236": [43,47]
                 }
  void_list_fin={"001": [43,53,123],
                 "002": [43,123],
                 "003": [43,123],
                 "004": [43,123],
                 "005": [43],
                 "006": [43,123],
                 "007": [43,123],
                 "008": [43,123],
                 "015": [43,123],
                 "016": [43,103,123],
                 "017": [43,123],
                 "018": [43,123],
                 "019": [43,123],
                 "020": [43,123],
                 "021": [43,123],
                 "022": [43,123],
                 "023": [43,123],
                 "024": [43,58,118,123],
                 "025": [43,78,123],
                 "026": [43,123],
                 "030": [43,123],
                 "031": [43,123],
                 "032": [43,123],
                 "033": [43,123],
                 "034": [43,123],
                 "035": [43,123],
                 "037": [43,123],
                 "038": [43,123],
                 "043": [43,123],
                 "045": [43,50,123],
                 "047": [43,58,123],
                 "048": [43,123],
                 "049": [48,57,123],
                 "052": [43,103,123],
                 "113": [43,123],
                 "144": [43,123],
                 "207": [43,123],
                 "209": [43,83,113,123],
                 "213": [43,48,55,57,65,123],
                 "227": [49],
                 "235": [43,49,123],
                 "236": [43,47]
                 }
  for i, col_ini in enumerate(void_list_ini[dict_id]):
    col_ini=col_ini-1
    col_fin=void_list_fin[dict_id][i]
    if re.compile(r"\S").search(line[col_ini:col_fin]):
      msg="These columns must be blank."
      print_error_2(dict_id,"",msg,line,col_ini,col_fin)

  return


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


def print_underline(col1,col2):
  char=" "*col1+"^"*(col2-col1)
  print(char)

  return


def print_error_2(dict_id,code,msg,line,col1,col2):
  if code=="":
    code="(dictionary header)"
  print("** Dict.{:3s} {:<30s}{:<50s}".format(dict_id,code,msg))
  print(line)
  print_underline(col1,col2)

  return


def print_error_3(dict_id,code,msg):
  print("** Dict.{:3s} {:<30s}{:<50s}".format(dict_id,code,msg))

  return


def print_error_fatal(msg,line):
  print("** "+msg)
  print(line)
  exit()


def get_file_lines(file):
  if os.path.exists(file):
    f=open(file, 'r')
    lines=f.read().splitlines()
    f.close()
  else:
    msg="File "+file+" does not exist."
    line=""
    print_error_fatal(msg,line)
  return lines


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
  dica2j()
  exit()

#Uniqueness checking of numerical equivalent within dictionary
# dictionary_num_eq_list=["001", "002",  "016", "030", "031", "032",
#                         "0331","0332", "034", "035", "209", "227"]
# num_eq_list=dict()
# for dict_id in dictionary_num_eq_list:
#   num_eq_list[dict_id]=[]

