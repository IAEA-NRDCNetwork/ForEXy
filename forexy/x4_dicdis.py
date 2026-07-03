#!/usr/bin/python3
ver="2026.06.24"
############################################################
# DICDIS Ver.2026.06.24
# (Production of dictionaries for distribution)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
############################################################
import argparse
import datetime
import json
import os
import re
import time
from datetime import timezone

def dicdis():
  args=get_args(ver)
  main(*get_input(args))


def main(dict_ver,dir_archive,dir_json,dir_dist,force0):
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

  time_now=datetime.datetime.now(timezone.utc)
  date_out=time_now.strftime("%Y%m")

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

  for dict_id in list(dictionary_list):
    for record in list(dict_json[dict_id]):
      code=get_code(dict_id,record)
      if code!="": # not a comment
        ind=get_index(dict_id,code)
        alteration_flag=dict_json[dict_id][ind]["alteration_flag"]
        if alteration_flag=="D":
          dict_json[dict_id].pop(ind)
        elif alteration_flag=="A" or\
             alteration_flag=="S" or\
             alteration_flag=="M":
          dict_json[dict_id][ind]["date"]=date_out
          dict_json[dict_id][ind]["alteration_flag"]=" "

# Produce JSON Dictionary for distribution
  json_out=json.dumps(dict_json,indent=2)
  file_out=dir_dist+"/dict_"+dict_ver+".json"
  print("printing JSON dictionary    ... ")
  f=open(file_out,'w')
  f.write(json_out)
  f.close()


# Produce Archive Dictionary
  print("printing Archive dictionary ... ", end="")
  print_archive(dir_archive,dir_dist,date_out,dictionary_list)


# Produce Backup Dictionary
  archive_to_backup(dir_dist,dict_ver,dictionary_list)

  time_end=time.time()
  time_elapsed=format(time_end-time_start, ".2f")
  print("DICDIS: Processing terminated normally. "+time_elapsed+" sec.\n")


# Print Archive Dictionary after updating/excluding flagged records
def print_archive(dir_archive,dir_dist,date_out,dictionary_list):
  file_in=dir_archive+"/dict_arc.top"
  lines=get_file_lines(file_in)
  file_out=dir_dist+"/dict_arc.top"
  print("top", end=", ")
  f=open(file_out,'w')

  for line in lines:
    f.write(line+"\n")
  f.close()

  for dict_id in dictionary_list:
    if re.compile("a$").search(dict_id):
      continue
    print(dict_id, end=" ")
    file_in=dir_archive+"/dict_arc_new."+dict_id
    lines=get_file_lines(file_in)
    file_out=dir_dist+"/dict_arc_new."+dict_id
    f=open(file_out,'w')
    out="y"
    for line in lines:
      alteration_flag=line[0:1]
      date=line[5:11]
      key=line[12:42]
      if re.compile(r"\S+").search(key):
        if  alteration_flag=="D":
          out="n"
        else:
          out="y"
          if alteration_flag=="A" or\
             alteration_flag=="S" or\
             alteration_flag=="M":
            line=line.replace(date,date_out)
      if out=="y":
        line=" "+line[1:123]
        f.write(line+"\n")
    f.close()
  print()
  print()


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
   usage="Prepare Archive, Backup and JSON Dictionaries for distribution",\
   epilog="example: x4_dicdis.py -n 9132 -a input -j json -o dist")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-n", "--dict_ver",\
   help="dictionary version (transmission ID)")
  parser.add_argument("-a", "--dir_archive",\
   help="directory of input Archive Dictionaries")
  parser.add_argument("-j", "--dir_json",\
   help="directory of input JSON Dictionary")
  parser.add_argument("-o", "--dir_dist",\
   help="directory of output dictionaries")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("DICDIS (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force
  dict_ver=args.dict_ver
  if dict_ver is None:
    dict_ver=input("dictionary version [9132] -----------------------> ")
    if dict_ver=="":
      dict_ver="9132"
  if not re.compile(r"^\d{4,4}$").search(dict_ver):
    print(" ** Dictionary version must be four-digit integer.")
  while not re.compile(r"^\d{4,4}$").search(dict_ver):
    dict_ver=input("dictionary version [9132] -----------------------> ")
    if dict_ver=="":
      dict_ver="9132"
    if not re.compile(r"^\d{4,4}$").search(dict_ver):
      print(" ** Dictionary version must be four-digit integer.")

  dir_archive=args.dir_archive
  if dir_archive is None:
    dir_archive=input("directory of input Archive Dictionaries [input] -> ")
    if dir_archive=="":
      dir_archive="input"
  if not os.path.exists(dir_archive):
    print(" ** Folder "+dir_archive+" does not exist.")
  while not os.path.exists(dir_archive):
    dir_archive=input("directory of input Archive Dictionaries [input] -> ")
    if dir_archive=="":
      dir_archive="input"
    if not os.path.exists(dir_archive):
      print(" ** Folder "+dir_archive+" does not exist.")

  dir_json=args.dir_json
  if dir_json is None:
    dir_json=input("directory of input JSON Dictionary [json] -------> ")
    if dir_json=="":
      dir_json="json"
  if not os.path.exists(dir_json):
    print(" ** Folder "+dir_json+" does not exist.")
  while not os.path.exists(dir_json):
    dir_json=input("directory of input JSON Dictionary [json] -------> ")
    if dir_json=="":
      dir_json="json"
    if not os.path.exists(dir_json):
      print(" ** Folder "+dir_json+" does not exist.")

  dir_dist=args.dir_dist
  if dir_dist is None:
    dir_dist=input("directory of output directories [dist] ----------> ")
  if dir_dist=="":
    dir_dist="dist";
  if not os.path.isdir(dir_dist):
    msg="Directionry '"+dir_dist+"' does not exist and must be created."
    print_error(msg,"",force0)
    os.mkdir(dir_dist)
  if os.path.isfile(dir_dist):
    msg="Directory '"+dir_dist+"' exists and must be overwritten."
    print_error(msg,"",force0)

  return dict_ver,dir_archive,dir_json,dir_dist,force0


def archive_to_backup(dir_dist,dict_ver,dictionary_list):
  nline=dict()
  for dict_id in dictionary_list:
    if re.compile("a$").search(dict_id):
      continue
    num="%3s" % int(dict_id)
    file_in=dir_dist+"/dict_arc_new."+dict_id
    lines=get_file_lines(file_in)
    nline[num]=0
    for line in lines:
      if not re.compile(r"\S+").search(line[12:42]):
        next
      elif line[1:4]=="DEL":
        next
      else:
        nline[num]+=1

  file_out=dir_dist+"/dan_back_new."+dict_ver
  print("printing backup dictionary  ... ")
  g=open(file_out,"w")
  lines=get_file_lines(dir_dist+"/dict_arc.top")
  for line in lines:
    num=line[0:3]
    line=line[0:83]+"%4s" % nline[num]
    print(line,file=g)
  print("",file=g)
  for dict_id in dictionary_list:
    if re.compile("a$").search(dict_id):
      continue
    num="%3s" % int(dict_id)
    file_in=dir_dist+"/dict_arc_new."+dict_id
    lines=get_file_lines(file_in)
    for line in lines:
      if dict_id=="001":
        line=line.replace(line[53:108]," "*55)
      elif dict_id=="025":
        line=line[0:93]+"   "+line[96:123]
      if line[1:4]=="DEL":
        next
      elif re.compile(r"\S+").search(line[12:42]):
        print(num+line,file=g)
  g.close()


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
  dicdis() 
  exit()
