#!/usr/bin/python3
ver="2026.09.26"
############################################################
# X4TOCX Ver.2026.09.26
# (Utility to convert EXFOR to CX4)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
############################################################
import argparse
import datetime
import glob
import os
import re
import time

if os.path.isfile("x4_x4toj4.py"):
  import x4_x4toj4
else:
  from forexy import x4_x4toj4

if os.path.isfile("x4_poipoi.py"):
  import x4_poipoi
else:
  from forexy import x4_poipoi

if os.path.isfile("x4_j4toc6.py"):
  import x4_j4toc6
else:
  from forexy import x4_j4toc6

if os.path.isfile("x4_c6tocx.py"):
  import x4_c6tocx
else:
  from forexy import x4_c6tocx

def x4tocx():
  args=get_args(ver)
  main(*get_input(args))


def main(file_x4,file_dict,entry,dir_out,file_idx,force0,sysout0,enewid0,email0,exclhi0,incder0):
  time_start=time.time()

  force=force0
  sysout=sysout0
  enewid=enewid0
  email=email0
  exclhi=exclhi0
  incder=incder0

  chkrid   = False  # record identificaiton not checked in X4TOJ4
  add19    = True   # add '19' to two-digit year
  keepflg  = False  # ignore flags at col.80 in X4TOJ4
  outstr   = False  # print real numbers as strings in X4TOJ4
  key_keep =["all"] # keep all keywords in X4TOJ4 and POIPOI
  delpoin  = False  # delete pointer in the output in POIPOI
  keep001  = False  # keep common subentry in POIPOI
  keepres  = False  # keep resonance parameter table in POIPOI
  outc4    = False  # output not to C4 but to C6 in J4TOC6
  seplvl   = 3      # separation level = 3 in J4TOC6

  time_now=datetime.datetime.now()
  dir_wrk = time_now.strftime('%Y%m%d%H%M%S%f')
  os.mkdir(dir_wrk)

# Conversion to J4 format by X4TOJ4
  file_js = "exfor.json"
  x4_x4toj4.main(file_x4,file_dict,file_js,key_keep,email,force,chkrid,add19,keepflg,outstr)

# Conversion to J4 format without pointer structure by POIPOI
  x4_poipoi.main(file_js,file_dict,"all",dir_wrk,key_keep,force,delpoin,keep001,keepres)
  os.remove(file_js)

# Check presence of J4 files
  entry_lower=entry.lower()
  pattern=dir_wrk+"/"+entry_lower+".[0-9][0-9][0-9]*.json"
  all_files=glob.glob(pattern)
  files = [file for file in all_files if re.search(r"\d\d\d(\.[A-Z1-9])?", file)]
  if len(files)==0:
    files=glob.glob("./"+dir_wrk+"/*")
    for file in files:
      os.remove(file)
    os.rmdir(dir_wrk)
    entry_upper=entry.upper() 
    print_error_fatal("The input EXFOR file does not include EXFOR# "+entry_upper+".", "")

# Conversion to C6 format by J4TOC6
  file_log="x4_x4toc6.txt"
  x4_j4toc6.main(dir_wrk,file_dict,entry_lower,dir_wrk,seplvl,file_log,sysout,enewid,force,exclhi,incder,outc4)
  os.remove(file_log)

# Conversion to CX4 format by C6TOCX
  pattern=dir_wrk+"/"+entry_lower+".[0-9][0-9][0-9]*.c6"
  files=glob.glob(pattern)
  for file_c6 in files:
    m=re.search(r"([0-8a-z]\d{4}\.\d{3}(\.[0-9a-z])?)-(.+?)\.c6",file_c6)
    if m:
      file1=m.group(1)
      file1=file1.upper()
      file2=m.group(3)
      file_cx4=dir_out+"/"+file2+"_"+file1+".cx4"
    else:
      msg="Input C6 file does not have the standard naming."
      print_error_fatal(msg,x4_json["title"])
    x4_c6tocx.main(file_c6,file_dict,file_cx4,file_idx,sysout,force)
    files=glob.glob("./"+dir_wrk+"/*")

  for file in files:
    os.remove(file)
  os.rmdir(dir_wrk)

  time_end=time.time()
  time_elapsed=format(time_end-time_start, ".2f")
  print("X4TOC6: Processing terminated normally. "+time_elapsed+" sec.\n")


def get_args(ver):
  parser=argparse.ArgumentParser(\
   usage="Convert EXFOR file to C6 file",\
   epilog="example: x4_x4tocx.py -i exfor.txt -e 22742 -o cx4")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-i", "--file_x4",\
   help="input EXFOR file")
  parser.add_argument("-d", "--file_dict",\
   help="input JSON dictionary (optional, default: dict.json)", default="dict.json")
  parser.add_argument("-e", "--entry",\
   help="EXFOR Entry number")
  parser.add_argument("-o", "--dir_out",\
   help="output CX4 directory")
  parser.add_argument("-n", "--file_idx",\
   help="output index file (optional, default: x4_x4tocx.txt)", default="x4_x4tocx.txt")
  parser.add_argument("-s", "--sysout",\
   help="reference system identifier (optional, default: OOO)", default="OOO")
  parser.add_argument("-w", "--enewid",\
   help="energy width allowance in percent for SACS (optional, default: 10)", default="10")
  parser.add_argument("-m", "--email",\
   help="your email address for addition of DOI (optional)", default=None)
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")
  parser.add_argument("-x", "--exclhi",\
   help="particle-induced reaction only", action="store_true")
  parser.add_argument("-y", "--incder",\
   help="include DERIVed data", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("X4TOC6 (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force
  exclhi0=args.exclhi
  incder0=args.incder

  file_x4=args.file_x4
  if file_x4 is None:
    file_x4=input("input EXFOR file [exfor.txt] -------------> ")
    if file_x4=="":
      file_x4="exfor.txt"
  if not os.path.exists(file_x4):
    print(" ** File "+file_x4+" does not exist.")
  while not os.path.exists(file_x4):
    file_x4=input("input EXFOR file [exfor.txt] -------------> ")
    if file_x4=="":
      file_x4="exfor.txt"
    if not os.path.exists(file_x4):
      print(" ** File "+file_x4+" does not exist.")

  file_dict=args.file_dict
  print("JSON Dictionary --------------------------> "+file_dict)
  if not os.path.exists(file_dict):
    print(" ** File "+file_dict+" does not exist.")
  while not os.path.exists(file_dict):
    file_dict=input("JSON Dictionary [dict.json] --------------> ")
    if file_dict=="":
      file_dict="dict.json"
    if not os.path.exists(file_dict):
      print(" ** File "+file_dict+" does not exist.")

  entry=args.entry
  if entry is None:
    entry=input("EXFOR Entry # [22742] --------------------> ")
    if entry=="":
      entry="22742"

  dir_out=args.dir_out
  if dir_out is None:
    dir_out=input("Directory of output CX4 files [cx4] ------> ")
  if dir_out=="":
    dir_out="cx4"
  if os.path.isdir(dir_out):
    msg="Directory '"+dir_out+"' exists and must be overwritten."
    print_error(msg,"",force0)
  else:
    msg="Directionry '"+dir_out+"' does not exist and must be created."
    print_error(msg,"",force0)
    os.mkdir(dir_out)

  file_idx=args.file_idx
  print("output index file ------------------------> "+file_idx)
  print("\n")
  if os.path.isfile(file_idx):
    msg="File '"+file_idx+"' exists and must be appended."
    print_error(msg,"",force0)

  sysout=args.sysout
  sysout=sysout.upper()
  if len(sysout)==2:
    sysout+="O"
  if not re.compile(r"^(O|L|C)(O|L|C)(O|L|C)$").search(sysout):
    print(" ** "+sysout+" is an invalid reference system identifier. Must be a combination of O, L and C.")
  while not re.compile(r"^(O|L|C)(O|L|C)(O|L|C)$").search(sysout):
    sysout=input("reference system identifier [ooo] ---------> ")
    if sysout=="":
      sysout="OOO"
    sysout=sysout.upper()
    if len(sysout)==2:
      sysout+="O"
    if not re.compile(r"^(O|L|C)(O|L|C)(O|L|C)$").search(sysout):
      print(" ** "+sysout+" is an invalid reference system identifier. Must be a combination of O, L and C.")

  enewid=args.enewid
  print("energy width allowance (%) for SACS ------> "+enewid)
  if is_float(enewid)==False:
    print(" ** "+enewid+" is not a number. Must be a real number or integer.")
    while is_float(enewid)==False:
      enewid=input("energy width allowance (%) for SACS [10] -> ")
      if enewid=="":
        enewid=10
      if is_float(enewid)==False:
        print(" ** "+enewid+" is not a number. Must be a real number or integer.")
  enewid=float(enewid)

  email=args.email
  if email is not None:
    print("your email address ------------------------> "+email)
    if not re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$").search(email):
      print(" ** Input a correct email address.")
    while not re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$").search(email):
      email=input("your email address ------------------------> ")
      if not re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$").search(email):
        print(" ** Input a correct email address.")


  return file_x4,file_dict,entry,dir_out,file_idx,force0,sysout,enewid,email,exclhi0,incder0


def is_float(s):
  try:
    float(s)
    return True
  except ValueError:
    return False


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


def print_error_fatal(msg,line):
  print("**  "+msg)
  print(line)
  exit()


if __name__ == "__main__":
  x4tocx()
  exit()
