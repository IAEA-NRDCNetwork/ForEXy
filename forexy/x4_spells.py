#!/usr/bin/python3
ver="2026.09.26"
############################################################
# SPELLS Ver.2026.09.26
# (Spell checker for free text in EXFOR)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
############################################################
# Install pyspellchecker by the following command:
#  pip install pyspellchecker
############################################################
import argparse
import datetime
import os
import re
import time
from spellchecker import SpellChecker
spell = SpellChecker()

def spells():
  args=get_args(ver)
  main(*get_input(args))


def main(file_x4,file_dict,file_typo,force0):
  time_start=time.time()

  global known_words

  force=force0

  time_now=datetime.datetime.now()
  time_out=time_now.strftime("%Y-%m-%d %H:%M:%S")

  known_words=[]
  lines=get_file_lines(file_dict)

  f=open(file_typo, 'w')
  f.write("           -------------------------------------------------------------------\n")
  f.write("           SPELLS report "+time_out+"\n")
  f.write("\n")
  f.write("             - unrecognized words in "+file_x4+"\n")
  f.write("           -------------------------------------------------------------------\n")
  f.write("\n")

  for line in lines:
    array=re.split(r"(,|\s)", line)
    for item in array:
      known_words.append(item)

  lines=get_file_lines(file_x4)
  typos=free_text_analyser(f,lines)

  num=dict()

  if (len(typos)>0):
    f.write("Unrecognized words:\n")
    typos.sort()
    typos_unique=list(dict.fromkeys(typos))
    for word in typos_unique:
      num[word]=typos.count(word)

    for typo in typos_unique:
      if (num[typo]==1):
        f.write(" "+typo+"\n")
      else:
        f.write(" "+typo+" x"+str(num[typo])+"\n")
    f.write("\n")

  f.close()

  lines=get_file_lines(file_typo)
  for line in lines:
    print(line, end="")

  time_end=time.time()
  time_elapsed=format(time_end-time_start, ".2f")
  print("SPELLS: Processing terminated normally. "+time_elapsed+" sec.\n")


def get_args(ver):

  parser=argparse.ArgumentParser(\
   usage="Check English spells in free text of EXFOR file",\
   epilog="example: x4_spells.py -i exfor.txt -o x4_spells_out.txt")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-i", "--file_x4",\
   help="input EXFOR file")
  parser.add_argument("-d", "--file_dict",\
   help="input known word dictionary (optional, default: x4_spells.dic)", default="x4_spells.dic")
  parser.add_argument("-o", "--file_typo",\
   help="output summary of typos")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print()
  print("SPELLS (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force

  file_x4=args.file_x4
  if file_x4 is None:
    file_x4=input("input EXFOR file [exfor.txt] ----------------> ")
    if file_x4=="":
      file_x4="exfor.txt"
  if not os.path.exists(file_x4):
    print(" ** File "+file_x4+" does not exist.")
  while not os.path.exists(file_x4):
    file_x4=input("input EXFOR file [exfor.txt] ---------------------> ")
    if file_x4=="":
      file_x4="exfor.txt"
    if not os.path.exists(file_x4):
      print(" ** File "+file_x4+" does not exist.")

  file_dict=args.file_dict
  print("input known word dictionary -----------------> "+file_dict)
  if file_dict is None:
    file_dict=input("input known word dictionary [x4_spells.dic] -> ")
    if file_dict=="":
      file_dict="x4_spells.dic"
  if not os.path.exists(file_dict):
    print(" ** File "+file_dict+" does not exist.")
  while not os.path.exists(file_dict):
    file_dict=input("input known word dictionary [x4_spells.dic] -> ")
    if file_dict=="":
      file_dict="x4_spells.dic"
    if not os.path.exists(file_dict):
      print(" ** File "+file_dict+" does not exist.")

  file_typo=args.file_typo
  if file_typo is None:
    file_typo=input("output typo list file [x4_spells.txt] -------> ")
  if file_typo=="":
    file_typo="x4_spells.txt"
  if os.path.isfile(file_typo):
    msg="File '"+file_typo+"' exists and must be overwritten."
    print_error(msg,"",force0)

  print()
  return file_x4,file_dict,file_typo,force0


def print_underline_multi(f,col1s,col2s):
  char=""
  ioff=0
  for i, col1 in enumerate(col1s):
    length=col2s[i]-col1
    char+=" "*(col1-ioff)+"^"*length
    ioff=col1+length
  f.write(char+"\n")


def get_file_lines(file):
  if os.path.exists(file):
    f=open(file, "r")
    lines=f.readlines()
    f.close()
  else:
    msg="File "+file+" does not exist."
    print_error_fatal(msg)
  return lines


# Extraction of free text
def free_text_analyser(f,lines):
  all_typos=[]
  sys_id="ENDENTRY"
  for line in lines:
    if re.compile("^BIB       ").search(line):
      sys_id="BIB"
      nparen=0
      code=""

    elif re.compile("^ENDBIB     ").search(line):
      sys_id="ENDBIB"

    elif sys_id=="BIB":
      content=line[11:66]
      (code,text,nparen)=code_extraction(content,code,nparen)
      if nparen==0:
        code=""
        all_typos=spell_checker(f,line,text,all_typos)

  return all_typos


def spell_checker(f,line,text,all_typos):
  words=re.split(r"(,|-|:|\s|\(|\))", text)
  typos=[]
  for i, word in enumerate(words):
    if re.compile("^[a-z]+$").search(word):
      result=spell.unknown([word])
      if len(result)==1 and word not in known_words:
        typos.append(word)
        all_typos.append(word)

  col1s=[]
  col2s=[]
  char=line
  for typo in typos:
    col1=char.find(typo)
    col2=col1+len(typo)
    col1s.append(col1)
    col2s.append(col2)
    length=len(typo)
    char=char.replace(typo,"X"*length,1)

  if len(typos)>0:
    line=line.rstrip("\n")
    f.write(line+"\n")
    print_underline_multi(f,col1s,col2s)

  return all_typos


def code_extraction(content,code,nparen):
  chars=list(content)
  nchar=0
  text=""
  for char in chars:
    if char=="(":
      nparen+=1
    elif char==")":
      nparen-=1
    if (nparen>0):
      nchar+=1
    if nparen==0:
      if nchar!=0:
        nchar+=1
      code+=content[0:nchar]
      text=content[nchar:]
      text=text.rstrip()
      return code, text, nparen
    else:
      text+=" "

  code+=content.rstrip()
  return code, "", nparen


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
  spells()
  exit()
