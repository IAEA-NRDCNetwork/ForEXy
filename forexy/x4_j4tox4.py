#!/usr/bin/python3
ver="2026.06.24"
############################################################
# J4TOX4 Ver.2026.06.24
# (Utility to convert J4 to EXFOR)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
############################################################
import argparse
import datetime
import json
import os
import re
import time

def j4tox4():
  args=get_args(ver)
  main(*get_input(args))


def main(file_j4,file_dict,file_x4,force0):
  time_start=time.time()

  global dict_json

  force=force0

  x4_json=read_x4json(file_j4)
  dict_json=read_dict(file_dict)

  f=open(file_x4,"w")

  keywords=["TRANS","MASTER","REQUEST","ENTRY"]
  for keyword in keywords:
    if keyword in x4_json:
      f.write("%-11s"  % keyword)
      f.write("%11s"   % x4_json[keyword]["N1"])
      f.write("%11s\n" % x4_json[keyword]["N2"])

      for nentry, entry in enumerate(x4_json["entries"]):
        print_entry(f,x4_json["entries"][nentry])

      keyword_end="END"+keyword
      f.write("%-11s"  % keyword_end)
      f.write("%11s"   % x4_json[keyword_end]["N1"])
      f.write("%11s\n" % x4_json[keyword_end]["N2"])

      break

  if keyword=="ENTRY":
    print_entry(f,x4_json["entries"][0])

  f.close()

  time_end=time.time()
  time_elapsed=format(time_end-time_start, ".2f")
  print("J4TOX4: Processing terminated normally. "+time_elapsed+" sec.\n")


def print_entry(f,x4_json):
  f.write("%-10s"  % "ENTRY")
  f.write("%1s"    % x4_json["ENTRY"]["alteration_flag"])
  f.write("%11s"   % x4_json["ENTRY"]["N1"])
  f.write("%11s"   % x4_json["ENTRY"]["N2"])
  f.write("%29s"   % "")
  if x4_json["ENTRY"]["transmission_identification"]!=None:
    f.write("%4s\n"   % x4_json["ENTRY"]["transmission_identification"])
  else:
    f.write("%4s\n"   % "")

  for nsubent, subentry in enumerate(x4_json["subentries"]):
    print_subent(f,x4_json["subentries"][nsubent])

  f.write("%-11s"  % "ENDENTRY")
  f.write("%11s"   % x4_json["ENDENTRY"]["N1"])
  f.write("%11s\n" % x4_json["ENDENTRY"]["N2"])

  return


def print_subent(f,x4_json):

  keywords=["SUBENT","ENDSUBENT","NOSUBENT",\
            "BIB","ENDBIB","NOBIB",\
            "ENDCOMMON","NOCOMMON",\
            "ENDDATA","NODATA"]

  for keyword in x4_json:

    if keyword in keywords:
      f.write("%-11s"  % keyword)
      f.write("%11s"   % x4_json[keyword]["N1"])
      f.write("%11s"   % x4_json[keyword]["N2"])
      f.write("%29s"   % "")
      if keyword=="SUBENT" or keyword=="NOSUBENT":
        if x4_json[keyword]["transmission_identification"]!=None:
          f.write("%4s\n"   % x4_json[keyword]["transmission_identification"])
        else:
          f.write("%4s\n"   % "")
      else:
        f.write("%4s\n"   % "")

    elif keyword=="COMMON":
      print_common_data(f,keyword,x4_json["COMMON"])

    elif keyword=="DATA":
      print_common_data(f,keyword,x4_json["DATA"])

    else:
      print_bib(f,keyword,x4_json[keyword])

  return


def print_bib(f,keyword,x4_json):
  f.write("%-10s"  % keyword)

  pointers=list(dict.fromkeys([x["pointer"] for x in x4_json]))
  for pointer in pointers:
    for i, item in enumerate(x4_json):
      if item["pointer"]==pointer:
        if i!=0:
          f.write("          ")
        if pointer=="":
          f.write(" ")
        else:
          f.write(pointer)
              
        if keyword=="ANG-SEC" or\
           keyword=="EN-SEC" or\
           keyword=="MOM-SEC":
          if item["coded_information"] is not None:

            f.write("("+item["coded_information"]["heading"]+",")
            f.write(item["coded_information"]["particle"]+")")


        elif keyword=="ASSUMED":
          if item["coded_information"] is not None:
            prefix=item["coded_information"]["heading"]+","
            coded_information=item["coded_information"]["reaction"]
            print_code_combination(f,keyword,prefix,coded_information)


        elif keyword=="DECAY-DATA":
          if item["coded_information"] is not None:
            print_decaydata(f,keyword,item["coded_information"])


        elif keyword=="DECAY-MON":
          if item["coded_information"] is not None:
            print_decaydata(f,keyword,item["coded_information"])


        elif keyword=="ERR-ANALYS":
          if item["coded_information"] is not None:

            char="("+item["coded_information"]["heading"]
            if item["coded_information"]["minimum_value"] is not None:
               char+=","+str(item["coded_information"]["minimum_value"])
            if item["coded_information"]["maximum_value"] is not None:
               char+=","+str(item["coded_information"]["maximum_value"])
            if item["coded_information"]["correlation_property"] is not None:
               char+=","+item["coded_information"]["correlation_property"]
            char=re.sub(",+$","",char)
            f.write(char+")")


        elif keyword=="FACILITY":
          if item["coded_information"] is not None:

            if item["coded_information"]["institute"] is not None:
              f.write("("+item["coded_information"]["facility"][0]+","+\
                          item["coded_information"]["institute"]+")")
            else:
              print_code(f,keyword,item["coded_information"]["facility"])


        elif keyword=="HALF-LIFE":
          if item["coded_information"] is not None:

            f.write("("+item["coded_information"]["heading"]+",")
            f.write(item["coded_information"]["nuclide"]+")")


        elif keyword=="HISTORY":
          if item["coded_information"] is not None:
            f.write("("+str(item["coded_information"]["date"]))
            if item["coded_information"]["history"] is not None:
              f.write(item["coded_information"]["history"])
            f.write(")")


        elif keyword=="INC-SOURCE":
          if item["coded_information"] is not None:
            if item["coded_information"]["reaction"] is not None:
              f.write("("+item["coded_information"]["incident_source"][0]+"=("+\
                          item["coded_information"]["reaction"]["code"]+"))")
            else:
              print_code(f,keyword,item["coded_information"]["incident_source"])


        elif keyword=="LEVEL-PROP":
          if item["coded_information"] is not None:
            char="("
            if item["coded_information"]["flag"] is not None:
              flag=str(item["coded_information"]["flag"])
              flag=re.sub(".0+$",".",flag)
              char+="("+flag+")"
            char+=item["coded_information"]["nuclide"]+","
            if item["coded_information"]["level_identification"] is not None:
              char+=item["coded_information"]["level_identification"]["field_identifier"]
              char+="="
              char+=str(item["coded_information"]["level_identification"]["value"])
              char+=","
            if item["coded_information"]["level_properties"] is not None:
              for property in item["coded_information"]["level_properties"]:
                char+=property["field_identifier"]
                char+="="
                if property["field_identifier"]=="SPIN":
                  spins=[]
                  for spin in property["value"]:
                    spin=str(spin)
                    spin=re.sub(".0$",".",spin)
                    spins.append(spin)
                  char+="/".join(spins)
                  char+=","
                elif property["field_identifier"]=="PARITY":
                  parities=[]
                  for parity in property["value"]:
                    parity=str(parity)
#                   parity=re.sub(".0$",".",parity)
                    parities.append(parity)
                  char+="/".join(parities)
                  char+=","
            char=re.sub(",+$","",char)
            char=char+")"
            f.write(char)


        elif keyword=="MONITOR":
          if item["coded_information"] is not None:
            if item["coded_information"]["heading"] is not None:
              prefix="("+item["coded_information"]["heading"]+")"
            else:
              prefix=""
            coded_information=item["coded_information"]["reaction"]
            print_code_combination(f,keyword,prefix,coded_information)


        elif keyword=="MONIT-REF":
          if item["coded_information"] is not None:
            f.write("(")
            if item["coded_information"]["heading"] is not None:
              f.write("("+item["coded_information"]["heading"]+")")
            if item["coded_information"]["author"] is not None:
              f.write(item["coded_information"]["author"]+",")
            else:
              f.write(",")
            if item["coded_information"]["subentry_number"] is not None:
              f.write(item["coded_information"]["subentry_number"]+",")
            else:
              f.write(",")
            f.write(item["coded_information"]["reference"]["code"])
            f.write(")")


        elif keyword=="RAD-DET":
          f.write("(")
          if item["coded_information"] is not None:
            if item["coded_information"]["flag"] is not None:
              flag=str(item["coded_information"]["flag"])
              flag=re.sub(".0+$",".",flag)
              char+="("+flag+")"
              f.write(char)
            f.write(item["coded_information"]["nuclide"])
            if len(item["coded_information"]["radiation_type"])!=0:
              f.write(",")
              radiation_types=item["coded_information"]["radiation_type"]
              f.write(",".join(radiation_types))
          f.write(")")


        elif keyword=="REFERENCE":
          if item["coded_information"] is not None:
            coded_information=item["coded_information"]
            prefix=""
            print_code_combination(f,keyword,prefix,coded_information)


        elif keyword=="REACTION":
          coded_information=item["coded_information"]
          prefix=""
          print_code_combination(f,keyword,prefix,coded_information)
                  

        elif keyword=="REL-REF":
          if item["coded_information"] is not None:
            f.write("("+item["coded_information"]["code"]+",")
            if item["coded_information"]["subentry_number"] is not None:
              f.write(item["coded_information"]["subentry_number"]+",")
            else:
              f.write(",")
            if item["coded_information"]["author"] is not None:
              f.write(item["coded_information"]["author"]+",")
            else:
              f.write(",")
            f.write(item["coded_information"]["reference"]["code"]+")")


        elif keyword=="SAMPLE":
          if item["coded_information"] is not None:
            f.write("("+item["coded_information"]["nuclide"]+","+\
                        item["coded_information"]["field_identifier"]+"="+\
                        str(item["coded_information"]["value"])+")")
          

        elif keyword=="STATUS":
          if item["coded_information"] is not None:

            if item["coded_information"]["subentry_number"] is not None:
              f.write("("+item["coded_information"]["status"][0]+","+\
          
                          item["coded_information"]["subentry_number"]+")")
            elif item["coded_information"]["author"] is not None:
              f.write("("+item["coded_information"]["status"][0]+",,"+\
                          item["coded_information"]["author"]+","+\
                          item["coded_information"]["reference"]["code"]+")")

            else:
              print_code(f,keyword,item["coded_information"]["status"])


        else:

          if item["coded_information"] is not None:
            print_code(f,keyword,item["coded_information"])
          

        if item["free_text"] is not None:
          print_free_text(f,item["free_text"])

  return



def print_common_data(f,keyword,x4_json):

  f.write("%-11s"  % keyword)
  f.write("%11s"   % x4_json["N1"])
  f.write("%11s\n" % x4_json["N2"])

  for i, pointer in enumerate (x4_json["pointer"]):
    if pointer=="":
      pointer_out=" "
    else:
      pointer_out=pointer
    f.write("%-10s"  % x4_json["heading"][i])
    f.write(pointer_out)
    if i!=0 and (i+1)%6==0:
      f.write("\n")
  if len(x4_json["pointer"])%6!=0:
    f.write("\n")
    
  for i, pointer in enumerate (x4_json["pointer"]):
    f.write("%-11s"  % x4_json["unit"][i])
    if i!=0 and (i+1)%6==0:
      f.write("\n")
  if len(x4_json["pointer"])%6!=0:
    f.write("\n")

  if keyword=="COMMON":
    for i, pointer in enumerate (x4_json["pointer"]):
      f.write("%-11s"  % x4_json["value"][i])
      if i!=0 and (i+1)%6==0:
        f.write("\n")
    if len(x4_json["pointer"])%6!=0:
      f.write("\n")

  elif keyword=="DATA":
    for j, line in enumerate (x4_json["value"]):
      for i, pointer in enumerate (x4_json["pointer"]):
        if x4_json["value"][j][i] is None:
          f.write("%-11s"  % " ")
        else:
          f.write("%-11s"  % x4_json["value"][j][i])
        if i!=0 and (i+1)%6==0:
          f.write("\n")
      if len(x4_json["pointer"])%6!=0:
        f.write("\n")
  return


def print_code(f,keyword,codes):
  code_out="("
  code_out_sav=""
  for j, code in enumerate(codes):
    if keyword=="EXP-YEAR":
      code=str(code)
    elif keyword=="FLAG":
      code=str(code)
      code=re.sub(".0+$",".",code)
    code_out+=code
    if len(codes)!=1 and j!=len(codes)-1:
      if keyword=="AUTHOR":
        code_out+=", "
      else:
        code_out+=","
    if j==len(codes)-1:
      len_max=54
    else:
      len_max=55
    if len(code_out)>len_max:
      f.write(code_out_sav+"\n")
      f.write("           ")
      if j==len(codes)-1:
        code_out=" "+code
      else:
        if keyword=="AUTHOR":
          code_out=" "+code+", "
        else:
          code_out=" "+code+","
    else:
      code_out_sav=code_out
  
  f.write(code_out+")")

  return


def print_code_combination(f,keyword,prefix,coded_information):
  if coded_information["unit_combination"]=="(%)":
    f.write("(")
    f.write(prefix)
    f.write(coded_information["code"])
    f.write(")")
  else:
    chars=list(coded_information["unit_combination"])
#   code_out=prefix
    code_out_sav=""
    nunit=0
    for i, char in enumerate(chars):
      if char=="%":
        code_out+=coded_information["code_unit"][nunit]["unit"]
        nunit+=1
      else:
        if i==0:
          code_out=char+prefix
        else:
          code_out+=char
        if char=="/" and chars[i+1]=="/": # //
          continue
        elif char=="=" or char=="+" or char=="-" or\
             char=="*" or char=="/" or i==len(chars)-1:
          if nunit==len(coded_information["code_unit"])-1:
            len_max=54
          else:
            len_max=55
          if len(code_out)>len_max:
            f.write(code_out_sav)
            f.write("\n           ")
            if i==len(chars)-1: # last line of the code string output
              f.write(code_out.replace(code_out_sav,""))
            else:
              code_out_sav=code_out.replace(code_out_sav,"")
              code_out=code_out_sav
          else:
            code_out_sav=code_out

#   if code_out!="":
#     f.write(code_out)

  return
                  

def print_decaydata(f,keyword,coded_information):

  char="("
  if keyword=="DECAY-DATA":
    if coded_information["flag"] is not None:
      char+="("+str(coded_information["flag"])+")"
  elif keyword=="DECAY-MON":
    if coded_information["heading"] is not None:
      char+="("+coded_information["heading"]+")"

  char+=(coded_information["nuclide"]+",")

  if coded_information["half-life"] is not None:
    char+=str(coded_information["half-life"]["value"])
    char+=coded_information["half-life"]["unit"]

  margin=" "*(11+len(char))

  if len(coded_information["radiation"])==0:
      char+=")"
      f.write(char)

  else:
    char+=","
    radiations=coded_information["radiation"]
    for i, radiation in enumerate(radiations):
      if i>0:
        char=margin
      if radiation["radiation_type"] is not None:
        char+=("/".join(radiation["radiation_type"]))+","
      else:
        char+=","
      if radiation["energy"] is not None:
        energies=[]
        for energy in radiation["energy"]:
          energy=str(energy)
          energies.append(energy)
        char+="/".join(energies)
      char+=","
      if radiation["intensity"] is not None:
        char+=str(radiation["intensity"])+","
      else:
        char+=","

      if i==len(radiations)-1:
        char=re.sub(",+$","",char)
        char+=")"
      else:
        char+="\n"

      f.write(char)


def print_free_text(f,texts):
  for j, text in enumerate(texts):
    if j!=0:
      f.write("           ")
    f.write(text+"\n")

  return


def get_file_lines(file):
  if os.path.exists(file):
    f=open(file, "r")
    lines=f.readlines()
    f.close()
  else:
    msg="File "+file+" does not exist."
    print_error_fatal(msg)
  return lines


def read_x4json(file_j4):
  f=open(file_j4)
  try:
    x4_json=json.load(f)
  except json.JSONDecodeError:
    msg=file_j4+" is not in JSON format."
    print_error_fatal(msg,"")

  if x4_json["title"][0:18]!="J4 - EXFOR in JSON":
    msg=file_j4+" is not an EXFOR in JSON."
    print_error_fatal(msg,"")

  f.close()
  return x4_json


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


def get_args(ver):

  parser=argparse.ArgumentParser(\
   usage="Convert J4 file to EXFOR file",\
   epilog="example: x4_j4tox4.py -i exfor.json -d dict.json -o exfor.txt")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-i", "--file_j4",\
   help="input J4 file")
  parser.add_argument("-d", "--file_dict",\
   help="input JSON dictionary")
  parser.add_argument("-o", "--file_x4",\
   help="output EXFOR file")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("J4TOX4 (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force

  file_j4=args.file_j4
  if file_j4 is None:
    file_j4=input("input J4 file [exfor.json] --------> ")
    if file_j4=="":
      file_j4="exfor.json"
  if not os.path.exists(file_j4):
    print(" ** File "+file_j4+" does not exist.")
  while not os.path.exists(file_j4):
    file_j4=input("input J4 file [exfor.json] --------> ")
    if file_j4=="":
      file_j4="exfor.json"
    if not os.path.exists(file_j4):
      print(" ** File "+file_j4+" does not exist.")

  file_dict=args.file_dict
  if file_dict is None:
    file_dict=input("input JSON Dictionary [dict.json] -> ")
    if file_dict=="":
      file_dict="dict.json"
  if not os.path.exists(file_dict):
    print(" ** File "+file_dict+" does not exist.")
  while not os.path.exists(file_dict):
    file_dict=input("input JSON Dictionary [dict.json] -> ")
    if file_dict=="":
      file_dict="dict.json"
    if not os.path.exists(file_dict):
      print(" ** File "+file_dict+" does not exist.")

  file_x4=args.file_x4
  if file_x4 is None:
    file_x4=input("output EXFOR file [exfor.txt] -----> ")
  if file_x4=="":
    file_x4="exfor.txt"
  if os.path.isfile(file_x4):
    msg="File '"+file_x4+"' exists and must be overwritten."
    print_error(msg,"",force0)

  return file_j4,file_dict,file_x4,force0


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

  return


def print_error_3(ansan,keyword,msg,line,col1,col2,offset):
  print("** "+ansan+": "+keyword+": "+msg)
  for i in range(offset):
    line=" "+line
  print(line.rstrip())
  col1=col1+offset
  col2=col2+offset
  print_underline(col1,col2)

  return


def print_error_fatal(msg,line):
  print("**  "+msg)
  print(line)
  exit()


def print_underline(col1,col2):
  char=" "*(col1-1)+"^"*(col2-col1+1)
  print(char)

  return


def check_character(ansan,keyword,line):
  permitted_character_list=[
  "+", "-", ".", ")", "(", "*", "/", "=", "'", ",", "%", "<", ">", ":",
  ";", "!", "?", "&", "#", "[", "]", '"', "~", "@", "{", "}", "|", " "]

  chars=list(line.rstrip())
  for char in chars:
    if not re.compile("[a-zA-Z0-9]").search(char):
      if char not in permitted_character_list:
        msg="Illegal character: "+char
        col1=line.find(char)+1
        print_error_3(ansan,keyword,msg,line,col1,col1,0)

  return


if __name__ == "__main__":
  j4tox4()
  exit()
