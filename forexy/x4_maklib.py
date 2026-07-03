#!/usr/bin/python3
ver="2026.06.24"
############################################################
# MAKLIB Ver.2026.06.24
# (Utility for production of a new library tape.)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
############################################################
import argparse
import datetime
import os
import re
import time

def maklib():
  args=get_args(ver)
  main(*get_input(args))


def  main(dir_storage,file_lib,tape_id,force0,add190,cut660,nodic0):
  time_start=time.time()

  global nodic
  global add19
  global cut66

  force=force0
  add19=add190
  cut66=cut660
  nodic=nodic0

  (nan,col80,area_ini,area_fin,line_out)=merge(file_lib,dir_storage)

  output(file_lib,tape_id,nan,col80,area_ini,area_fin,line_out)

  time_end=time.time()
  time_elapsed=format(time_end-time_start, ".2f")
  print("MAKLIB: Processing terminated normally. "+time_elapsed+" sec.\n")

def output(file_lib,tape_id,nan,col80,area_ini,area_fin,line_out):
  f=open(file_lib,"w")

  n1="   {:>8s}".format(tape_id)
  time=datetime.datetime.now()
  date=time.strftime("%Y%m%d")
  n2="   {:8s}".format(date)
  n3n4n5="                                 "
  if cut66:
    f.write("LIB        "+n1+n2+"\n")
  elif col80:
    f.write("LIB        "+n1+n2+n3n4n5+area_ini+"000000000000 \n")
  else:
    f.write("LIB        "+n1+n2+"\n")

  for line in line_out:
    f.write(line)

  n1="{:>11d}".format(nan)
  n2="{:>11s}".format("0")
  if cut66:
    f.write("ENDLIB     "+n1+"\n")
  elif col80:
    f.write("ENDLIB     "+n1+"          0"+n3n4n5+area_fin+"999999999999 \n")
  else:
    f.write("ENDLIB     "+n1+"\n")

  f.close()

def merge(file_lib,dir_storage):
  entries=list()
  line_out=list()
  col80=True
  dirs=os.listdir(dir_storage)
  for dir in dirs:
    if os.path.isdir(dir_storage+"/"+dir):
      if re.compile("^[a-zA-Z0-9]$").search(dir):
        files=os.listdir(dir_storage+"/"+dir)
        for file in files:
          if re.compile(dir+r"\d{4}\.txt").search(file):
            entry=dir_storage+"/"+dir+"/"+file
            entries.append(entry)

  entries=sorted(entries)
  nan=0
  area_ini=""
  for i, entry in enumerate(entries):
    if nodic and entry.endswith("90001.txt"):
      continue
    nan+=1
    print("adding ..."+entry)
    with open(entry) as g:
      for line in g:
        if col80 and len(line)<80:
          col80=False
        if re.compile("^ENTRY").search(line):
          if i==0:
            area_ini=line[17:18]
          if i==len(entries)-1:
            area_fin=line[17:18]
        if add19 and\
          re.compile("^(ENTRY|SUBENT|NOSUBENT)").search(line):
          if line[25:27]=="  " and line[27:33]!="      ":
            line=line[0:25]+"19"+line[27:66]
        if cut66:
          if len(line)>79:
            line=line[0:66].rstrip()
            line=line.rstrip()
            line=line+"\n"
          if re.compile("^END(BIB|COMMON|DATA|SUBENT|ENTRY|DICT)").search(line):
            line=line[0:22]+"\n" # Delete N2=0
            
        line_out.append(line)

  if area_ini=="":
    msg="EXFOR entry not found. Check if the entry storage directory name is correct"
    print_error_fatal(msg,line)
    
  return nan,col80,area_ini,area_fin,line_out


def get_args(ver):

  parser=argparse.ArgumentParser(\
          usage="Production of a library tape",\
          epilog="example: x4_maklib.py -d entry -l library.txt -i 0001")
  parser.add_argument("-v", "--version",\
         action="version", version=ver)
  parser.add_argument("-d", "--dir_storage",\
   help="input entry storage directory")
  parser.add_argument("-l", "--file_lib",\
   help="output library tape")
  parser.add_argument("-i", "--tape_id",\
   help="tape ID")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")
  parser.add_argument("-a", "--add19",\
   help="addition of '19' to N2 ", action="store_true")
  parser.add_argument("-c", "--cut66",\
   help="delete cols.67-80 and trailing blanks before col.67", action="store_true")
  parser.add_argument("-n", "--nodic",\
   help="exclusion of dictionary ", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("MAKLIB (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force
  add190=args.add19
  cut660=args.cut66
  nodic0=args.nodic

  dir_storage=args.dir_storage
  if dir_storage is None:
    dir_storage=input("directory of input entry storage [entry] -> ")
    if dir_storage=="":
      dir_storage="entry"

  if not os.path.isdir(dir_storage):
    print(" ** Directory '"+dir_storage+"' does not exist.")
  while not os.path.isdir(dir_storage):
    dir_storage=input("directory of input entry storage [entry] -------> ")
    if dir_storage=="":
      dir_storage="entry"
    if not os.path.isdir(dir_storage):
      print(" ** Directory '"+dir_storage+"' does not exist.")

  file_lib=args.file_lib
  if file_lib is None:
    file_lib=input("output library tape [library.txt] --------> ")
    if file_lib=="":
      file_lib="library.txt"

  if os.path.isfile(file_lib):
    msg="The tape '"+file_lib+"' exists and must be deleted."
    print_error(msg,"",force0)
    os.remove(file_lib)

  tape_id=args.tape_id
  if tape_id is None:
    tape_id=input("Tape ID [0001] ---------------------------> ")
    if tape_id=="":
      tape_id="0000"

  return dir_storage,file_lib,tape_id,force0,add190,cut660,nodic0


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
  maklib()
  exit()
