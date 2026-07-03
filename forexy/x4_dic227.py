#!/usr/bin/python3
ver="2026.06.24"
############################################################
# DIC227 Ver.2026.06.24
# (Converter from Nubase to Archive Dictionary 227)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
############################################################
import argparse
import datetime
import os
import re
import time

def dic227():
  args=get_args(ver)
  main(*get_input(args))

def main(file_nubase,file_suppl,file_arc227,force0):
  time_start=time.time()

  force=force0

  amu=931494.10242 # 1 keV/u

  lines=get_file_lines(file_nubase)

  time_now=datetime.datetime.now()
  date_out=time_now.strftime("%Y%m")

  line_dic=dict()

  for line in lines:

    if re.compile("^#").search(line):
      continue

    mass=line[0:3] # mass number
    mass=re.sub("^0+","",mass)

    elem=line[4:7] # atomic number
    if elem=="000": # neutron
      elem="0"
    else:
      elem=re.sub("^0+","",elem)

    char=int(line[7:8]) # isomeric state (0: G, i: Mi)
    if char==0:
      isom=0

    symb=line[11:16] # symbol
    if re.compile("1n").search(symb):
      symb="NN"
    else:
      regex=re.compile("^{}".format(mass))
      symb=regex.sub("",symb)
      symb=re.sub(r"\s+$","",symb)
      symb=symb.upper()

    isou=line[67:68] # isomeric uncertain

    if isou=="*" and isom==0: # g.s. but g.s. and m.s. ordering uncertain)
      code=elem+"-"+symb+"-"+mass
    elif float(isom)>0:       # a metastable state
      code=elem+"-"+symb+"-"+mass+"-M"
    else:
      code=elem+"-"+symb+"-"+mass
    code="%-12s" % code

    if symb=="NN":
      asmb="N     "
    else:
      asmb=symb+mass
      asmb=re.sub(r"\s","",asmb)
      asmb="%-6s" % asmb

    spin_parity=line[88:102] # spin/parity

    if "#" in spin_parity or "(" in spin_parity: # strong experimental argument
      parity=" "
      spin="     "
    else:
      spin_parity=re.sub(r"\*","",spin_parity) # excluding the directly meausred flag *
      match=re.match(r"\d+(\/\d+)?(\+|-)?", spin_parity)
      if match==None:
        parity=" "
        spin="     "
      else:
        spin_parity=match.group()
        if spin_parity[-1]=="-" or spin_parity[-1]=="+":
          spin=spin_parity[0:-1]
          parity=spin_parity[-1]
        else:
          spin=spin_parity
          parity=" "
        if "/" in spin:
          arrays=spin.split("/") 
          spin=float(arrays[0])/float(arrays[1])
        else:
          spin=spin+".0"
        spin="%-5s" % spin

    hlf=line[69:78] # half-life value
    un1=line[78:79] # half-life unit (1st char)
    if un1=="m":
      fac=1.E-03
    elif un1=="u":
      fac=1.E-06
    elif un1=="n":
      fac=1.E-09
    elif un1=="p":
      fac=1.E-12
    elif un1=="f":
      fac=1.E-15
    elif un1=="a":
      fac=1.E-18
    elif un1=="z":
      fac=1.E-21
    elif un1=="y":
      fac=1.E-24
    elif un1=="k":
      fac=1.E+03
    elif un1=="M":
      fac=1.E+06
    elif un1=="G":
      fac=1.E+09
    elif un1=="T":
      fac=1.E+12
    elif un1=="P":
      fac=1.E+15
    elif un1=="E":
      fac=1.E+18
    elif un1=="Z":
      fac=1.E+21
    elif un1=="Y":
      fac=1.E+24
    elif un1==" ":
      fac=1

    un2=line[79:80] # half-life unit (2nd char)
    if un2=="s":
      fac=fac*1
    elif un2=="m":
      fac=fac*60
    elif un2=="h":
      fac=fac*3600
    elif un2=="d":
      fac=fac*86400
    elif un2=="y":
      fac=fac*31556926

    if hlf==" stbl    ": # T1/2=0 for stable nuclide (This must be first selection. e.g., 180Ta)
      hlfv=0
      hlf="           "
      dflag="S"
    elif not re.compile(r"\S").search(hlf): # T1/2 not given
      hlfv=0
      hlf="           "
      dflag="U"
    elif hlf==" p-unst  ": # T1/2=blank for particle unstable state
      hlfv=0
      hlf="           "
      dflag="P"
    elif "<" in hlf:       # T1/2 upper boundary given
      hlfv=0
      hlf="           "
      dflag="U"
    elif "#" in hlf:       # T1/2 from systematics
      hlfv=0
      hlf="           "
      dflag="U"
    elif ">" in hlf:       # T1/2 lower boundary given
      hlfv=re.sub(r"(>|~|\s)","",hlf)
      hlfv=float(hlfv)*fac
      hlf="           "
      dflag="U"
    else:                  # T1/2 for addition in Dict.
      hlf=re.sub("~","",hlf)
      hlf=float(hlf)*fac
      hlf="%11.4E" % hlf
      hlfv=hlf
      dflag="U"

    if isom!=0:  # not a g.s.
#     if dflag==" ":     # stable isomer (180Ta)
      if dflag=="S":     # stable isomer (180Ta)
        pass
      elif not re.compile(r"\d").search(hlf): # T1/2 not given
        if hlfv>=1: # state having lower boundary or systematic value is kept
          msg="Warning: Lower boundary or systematics value is given for T1/2"
          print_error(msg,line,force)
        else:
          continue
      elif float(hlf)<0.1:          # T1/2<0.1 sec
        continue

    arrays=line[119:209].split(";") # isotopic abundance (IT probablity ignored)
    abun=""
    for item in arrays:
      item=re.sub(r"\s\d+","",item) # remove uncertaity
      if re.compile(r"^IS=((\d|\+|-|\.)+)$").search(item):
        abun=re.search(r"(\d|\+|-|\.)+",item).group()
        if not re.compile(r"^\d+(\.\d+)?$").search(abun):
          msg="Error: Isotopic abundance is not a fixed decimal pointer number!"
          print_error_fatal(msg,line)
        abun="%11.4E" % float(abun)
   
      if not re.compile(r"\d").search(abun):
        abun="           "
  
    nume=10000*int(elem)+10*int(mass)+isom # Internal numerical equivalent
    nume="%7s" % nume
    isom+=1
   
    amas=line[18:31] # Mass excess
    if "#" in amas: # mass excess from systematics
      mflag="#"
      amas=re.sub(r"#","",amas)
    else:
      mflag=" "
    if re.compile(r"\d").search(amas):
      amas=float(re.sub(r"\s","",amas))
      amas=(amas+float(mass)*amu)/amu # Mass excess -> Atomic mass (in amu)
      if amas<10:
        amas="%.10f" % amas
      elif amas<100:
        amas="%.9f" % amas
      else:
        amas="%.8f" % amas
    else:
      amas="           "

    eexc=line[42:54] # excitation energy
    if "#" in eexc: # mass excess from systematics
      eflag="#"
      eexc=re.sub(r"#","",eexc) 
      eexc="%12.6f" % float(eexc)
    elif re.compile(r"\d").search(eexc):
      eflag=" "
      eexc="%12.6f" % float(eexc)
    else:
      eflag=" "
      eexc="            "
   
    char="MTRA "+date_out+" "
    char+=code
    char+="                   "
    char+=asmb
    char+=nume
    char+=" "    # Use flag
    char+=parity
    char+=spin
    char+=isou
    char+=hlf
    char+=dflag  # half-life unit (U: unstable, P: particle unstable)
    char+=mflag
    char+=eflag
    char+=abun
    char+=amas
    char+=eexc
    if nume in line_dic:
      msg="Error: Internal numerical equivalent is defined twice!"
      print_error_fatal(msg,line)
    else:
      line_dic[nume]=char

  numes=line_dic.keys()
  numes=sorted(numes)

  array=[]
  niso=dict()
  for nume in numes:
    asmb=line_dic[nume][43:49]
    if asmb in niso and re.compile(r"\w").search(asmb):
      niso[asmb]+=1 # g.s./m.s. counter for each (Z,A)
    else:
      niso[asmb]=0
    array.append(line_dic[nume])

# addition of -G and replacement of -M with -M1 etc.
  line_out=dict()
  iout=dict()
  for item in array:
    code=item[12:25]
    code_org=code

#   if not re.compile(r"-A\s*$").search(code): # isomeric flagging -G, -M1 and -M2
    asmb=item[43:49]
    if niso[asmb]>0 and not re.compile(r"-M\s*$").search(code): # g.s. for which a m.s. exists
      code=re.sub(r"\s+$","",code)
      code=code+"-G"
    elif niso[asmb]>1 and re.compile(r"-M\s*$").search(code):   # m.s. for which several m.s. exist
      if asmb in iout:    # 2nd, 3rd, ... m.s.
        iout[asmb]+=1
      else:               # 1st m.s.
        iout[asmb]=1
   
      code=re.sub(r"\s+$","",code)
      code+=str(iout[asmb])


#   code=re.sub(\s+$,"",code)
    code="%-13s" % code

# To set the last digit of the Z number at col.15
    elem=re.search(r"^\d+",code).group()
    if float(elem)<10:
      code=re.sub("  $","",code)
      code="  "+code
    elif float(elem)<100:
      code=re.sub(" $","",code)
      code=" "+code
    
    nume=item[49:56]
    line_out[nume]=re.sub(code_org,code,item) # addition of flag


# Addition of particles and natural isotopic mixtures
  lines=get_file_lines(file_suppl)

  for line in lines:
    if re.compile(r"\d").search(line[89:101]):
      amas=float(line[89:101])
      if amas<10:
        amas="%.10f" % amas
      elif amas<100:
        amas="%.9f" % amas
      else:
        amas="%.8f" % amas
    else:
      amas="            "
    char=line[0:43]+"      "+line[49:89]+amas+line[101:123] # removal of the symbol
    nume=line[49:56]

    if nume in line_out:
      msg="Error: Internal numerical equivalent is defined twice!"
      print_error_fatal(msg,line)
    else:
      line_out[nume]=char


# Final output
  f=open(file_arc227,'w')
  
# f.write("----+----1----+----2----+----3----+----4----+----5----+----6")
# f.write("----+----7----+----8----+----9----+----0----+----1----+----2---\n")

  numes=line_out.keys()
  numes=[int(i) for i in numes]
  numes=sorted(numes)
  numes=[str(i) for i in numes]
  numes=["{0:>7}".format(i) for i in numes]

  for nume in numes:
    char=line_out[nume][0:43]+"      "+line_out[nume][49:123] # output of A-symbol suspended
    char="%-123s" % char
    f.write(char+"\n")

  f.close()

  time_end=time.time()
  time_elapsed=format(time_end-time_start, ".2f")
  print("DIC227: Processing terminated normally. "+time_elapsed+" sec.\n")


def get_args(ver):
  parser=argparse.ArgumentParser(\
   usage="Convert NUBASE to Archive Dictionary 227",\
   epilog="example: x4_dic227.py -i nubase_4.mas20.txt -s dict_arc_sup.227 -o dict_arc_new.227")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-i", "--file_nubase",\
   help="input NUBASE file")
  parser.add_argument("-s", "--file_suppl",\
   help="input supplemental dictionary file")
  parser.add_argument("-o", "--file_arc227",\
   help="output Archive Dictionary file (optional)", default="dict_arc_new.227")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("DIC227 (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force

  file_nubase=args.file_nubase
  if file_nubase is None:
    file_nubase=input("input Nubase file [nubase_4.mas20.txt] ----------------> ")
    if file_nubase=="":
      file_nubase="nubase_4.mas20.txt"
  if not os.path.isfile(file_nubase):
    print(" ** File "+file_nubase+" does not exist.")
  while not os.path.isfile(file_nubase):
    file_nubase=input("input Nubase file [nubase_4.mas20.txt] ----------------> ")
    if file_nubase=="":
      file_nubase="nubase_4.mas20.txt"
    if not os.path.isfile(file_nubase):
      print(" ** File "+file_nubase+" does not exist.")

  file_suppl=args.file_suppl
  if file_suppl is None:
    file_suppl=input("input supplemental dictionary file [dict_arc_sup.227] -> ")
    if file_suppl=="":
      file_suppl="dict_arc_sup.227"
  if not os.path.isfile(file_suppl):
    print(" ** File "+file_suppl+" does not exist.")
  while not os.path.isfile(file_suppl):
    file_suppl=input("input supplemental file [dict_arc_sup.227] -> ")
    if file_suppl=="":
      file_suppl="dict_arc_sup.227"
    if not os.path.isfile(file_suppl):
      print(" ** File "+file_suppl+" does not exist.")

  file_arc227=args.file_arc227
  print("output Archive Dictionary file ------------------------> "+file_arc227)
  print("\n")
  if os.path.isfile(file_arc227):
    msg="File '"+file_arc227+"' exists and must be overwritten."
    print_error(msg,"",force0)

  return file_nubase,file_suppl,file_arc227,force0


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
  dic227()
  exit()
