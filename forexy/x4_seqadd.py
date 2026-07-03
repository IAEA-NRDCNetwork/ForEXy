#!/usr/bin/python3
ver="2026.06.24"
############################################################
# SEQADD Ver.2026.06.24
# (Utility for addition of record identification etc.)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
############################################################
import argparse
import datetime
import os
import re
import time

def seqadd():
  args=get_args(ver)
  main(*get_input(args))


def main(file_inp,file_out,force0,no19ad0,deltid0):
  time_start=time.time()

  global nbib
  global nkey
  global ncom
  global mcom
  global nrec
  global ndat
  global mdat
  global nlin
  global nsan
  global deltid
  global no19ad

  force=force0
  no19ad=no19ad0
  deltid=deltid0

  nsan=dict() # number of subentries
  nrec=dict() # number of records in the subentry
  nbib=dict() # number of records in BIB section
  nkey=dict() # number of keywords in BIB section
  ncom=dict() # number of records in COMMON section
  mcom=dict() # number of data fields in COMMON section
  ndat=dict() # number of records in DATA section
  mdat=dict() # number of data fields in DATA section
  nlin=dict() # number of data lines in DATA section

  nan=count(file_inp)
  output(file_inp, file_out, nan)

  time_end=time.time()
  time_elapsed=format(time_end-time_start, ".2f")
  print("SEQADD: Processing terminated normally. "+time_elapsed+" sec.\n")


def output(file_inp, file_out, nan):

  n3n4n5= "                                 "
  n3n4n5t="                             "
  g=open(file_inp,"r")
  f=open(file_out,"w")
  irec=0
  sec=""
  area=""
  an_last="00000"
  
  for i,line in enumerate(g):
    line=line.rstrip("\n")
    line="{:<66s}".format(line)
    key="{:<10s}".format(line[0:10])
    alt="{:>1s}".format(line[79:80])+"\n"

    if i==0:
      if key=="LIB       " or\
         key=="REQUEST   " or\
         key=="BACKUP    " or\
         key=="MASTER    ":
        inp_typ="LIB"
      elif key=="TRANS     ":
        inp_typ="TRA"
      elif key=="ENTRY     ":
        inp_typ="ENT"
      elif key=="DICTION   ":
        inp_typ="DIC"

      if (inp_typ=="ENT" and nan>1) or inp_typ=="DIC":
      
          area=line[17:18]
          time=datetime.datetime.now()
          date=time.strftime("%Y%m%d")
         
          cont="TRANS      "
          n1="       "+area+"???"
          n2="   {:8s}".format(date)
          seq=area+"000000000000"
          f.write(cont+n1+n2+n3n4n5+seq+" \n")

    if (key=="LIB       " or\
          key=="REQUEST   " or\
          key=="BACKUP    " or\
          key=="MASTER    ") and\
          sec!="DIC":
      cont=line[0:11]
      n1=line[11:22]
      n2=line[22:33]
      seq="1000000000000"
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif (key=="ENDREQUEST" or\
          key=="ENDLIB    "   or\
          key=="ENDBACKUP "   or\
          key=="ENDMASTER ") and\
          sec!="DIC":
      cont=line[0:11]
      n1="{:>11d}".format(nan)
      n2="{:>11s}".format("0")
      seq=area+"999999999999"
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif key=="TRANS     " and sec!="DIC":
      time=datetime.datetime.now()
      date=time.strftime("%Y%m%d")

      cont=line[0:11]
      area=line[18:19]
      n1=line[11:22]

      if area=="9":
        n2="     {:6s}".format(date[0:6])
      else:
        n2="   {:8s}".format(date)

      seq=area+"000000000000"
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif key=="ENDTRANS  " and sec!="DIC":
      cont=line[0:11]
      n1="{:>11d}".format(nan)
      n2="{:>11s}".format("0")
      seq=area+"999999999999"
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif (key=="ENTRY     " and sec!="DIC") or key=="DICTION   ":
      irec=0
      sec=""
      an=line[17:22]
      if an<=an_last:
        msg="Entry number smaller than the preceding entry number "+an_last
      else:
        an_last=an
        san_last=an+"000"
      area=line[17:18]
      cont=line[0:11]
      n1=line[11:22]
      if line[24:26]=="  " and not no19ad:
        n2="   19"+line[27:33]
      else:
        n2=line[22:33]
      seq=an+"00000001"
      print("writing ... "+an)
      if not deltid:
        tidN6=line[62:66]
        f.write(cont+n1+n2+n3n4n5t+tidN6+seq+alt)
      else:
        f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif (key=="ENDENTRY  " and sec!="DIC") or key=="ENDDICTION":
      cont=line[0:11]
      if no19ad:
        n1=line[11:22]
      else:
        n1="{:>11d}".format(nsan[an])
      n2="{:>11s}".format("0")
      seq=an+"99999999"
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif (key=="SUBENT    " and sec!="DIC") or key=="SUBDICT   ":
      irec=1
      san=line[14:22]
      an=line[14:19]
      if an!=an_last:
        msg="Subentry number inconsistent with the preceding entry number "+an_last
        print_error_fatal(msg,line)
      elif san<=san_last:
        msg="Subentry number inconsistent with the preceding subentry number "+san_last
        print_error_fatal(msg,line)
      else:
        san_last=san
      cont=line[0:11]
      n1=line[11:22]
      if line[24:26]=="  " and not no19ad:
        n2="   19"+line[27:33]
      else:
        n2=line[22:33]
      seq=san+"{:0>5d}".format(irec)

      if key=="SUBDICT   ":
        sec="DIC";
        desc=line[33:66]
        f.write(cont+n1+n2+desc+seq+alt)
      else:
        if not deltid:
          tidN6=line[62:66]
          f.write(cont+n1+n2+n3n4n5t+tidN6+seq+alt)
        else:
          f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif (key=="ENDSUBENT " and sec!="DIC") or key=="ENDSUBDICT":
      if key=="ENDSUBDICT":
        sec=""
      cont=line[0:11]
      if no19ad:
        n1=line[11:22]
      else:
        n1="{:>11d}".format(nrec[san])
      n2="{:>11s}".format("0")
      seq=san+"99999"
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif key=="NOSUBENT  " and sec!="DIC":
      san=line[14:22]
      an=line[14:19]
      if an!=an_last:
        msg="Subentry number inconsistent with the preceding entry number "+san
        print_error_fatal(msg,line)
      elif san<=san_last:
        msg="Subentry number inconsistent with the preceding subentry number "+san_last
        print_error_fatal(msg,line)
      else:
        san_last=san
      cont=line[0:11]
      n1=line[11:22]
      if re.compile(r"\S").search(line[27:33]):
        if line[24:26]=="  " and not no19ad:
          n2="   19"+line[27:33]
        else:
          n2=line[22:33]
      else:
        n2="           ";
      seq=san+"00001"
      if not deltid:
        tidN6=line[62:66]
        f.write(cont+n1+n2+n3n4n5t+tidN6+seq+alt)
      else:
        f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif key=="BIB       " and sec!="DIC":
      irec+=1
      sec="BIB"
      cont=line[0:11]
      if no19ad:
        n1=line[11:22]
        n2=line[22:33]
      else:
        n1="{:>11d}".format(nkey[san])
        n2="{:>11d}".format(nbib[san])
      seq=san+"{:0>5d}".format(irec)
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif key=="ENDBIB    " and sec!="DIC":
      irec+=1
      sec=""
      cont=line[0:11]
      if no19ad:
        n1=line[11:22]
      else:
        n1="{:>11d}".format(nbib[san])
      n2="{:>11s}".format("0")
      seq=san+"{:0>5d}".format(irec)
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif key=="NOBIB     " and sec!="DIC":
      irec+=1
      cont=line[0:11]
      if no19ad:
        n1=line[11:22]
      else:
        n1="{:>11s}".format("0")
      n2="{:>11s}".format("0")
      seq=san+"{:0>5d}".format(irec)
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif key=="COMMON    " and sec!="DIC":
      irec+=1
      sec="COM"
      cont=line[0:11]
      if no19ad:
        n1=line[11:22]
        n2=line[22:33]
      else:
        n1="{:>11d}".format(mcom[san])
        n2="{:>11d}".format(ncom[san])
      seq=san+"{:0>5d}".format(irec)
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif key=="ENDCOMMON " and sec!="DIC":
      irec+=1
      sec=""
      cont=line[0:11]
      if no19ad:
        n1=line[11:22]
      else:
        n1="{:>11d}".format(ncom[san])
      n2="{:>11s}".format("0")
      seq=san+"{:0>5d}".format(irec)
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif key=="NOCOMMON  " and sec!="DIC":
      irec+=1
      cont=line[0:11]
      if no19ad:
        n1=line[11:22]
      else:
        n1="{:>11s}".format("0")
      n2="{:>11s}".format("0")
      seq=san+"{:0>5d}".format(irec)
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif key=="DATA      " and sec!="DIC" and sec!="DAT":
      irec+=1
      sec="DAT"
      cont=line[0:11]
      if no19ad:
        n1=line[11:22]
        n2=line[22:33]
      else:
        n1="{:>11d}".format(mdat[san])
        n2="{:>11d}".format(nlin[san])
      seq=san+"{:0>5d}".format(irec)
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif key=="ENDDATA   " and sec!="DIC":
      irec+=1
      sec=""
      cont=line[0:11]
      if no19ad:
        n1=line[11:22]
      else:
        n1="{:>11d}".format(ndat[san])
      n2="{:>11s}".format("0")
      seq=san+"{:0>5d}".format(irec)
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    elif key=="NODATA    " and sec!="DIC":
      irec+=1
      cont=line[0:11]
      if no19ad:
        n1=line[11:22]
      else:
        n1="{:>11s}".format("0")
      n2="{:>11s}".format("0")
      seq=san+"{:0>5d}".format(irec)
      f.write(cont+n1+n2+n3n4n5+seq+alt)

    else:
      irec+=1
      cont=line[0:66]
      seq=san+"{:0>5d}".format(irec)
      f.write(cont+seq+alt)

    if irec>99999:
      msg="A subentry may not have more than 99999 lines."
      print_error_fatal(msg,line)


  if (inp_typ=="ENT" and nan>1) or inp_typ=="DIC":
    cont="ENDTRANS   "
    n1="{:>11d}".format(nan)
    n2="{:>11s}".format("0")
    seq=area+"999999999999"
    f.write(cont+n1+n2+n3n4n5+seq+alt)


def count(file_inp):
  nan=0
  san=""
  sec=""
  f=open(file_inp,"r")

  sysid="          "
  for i,line in enumerate(f):
    line=line.rstrip("\n")
    key="{:<10s}".format(line[0:10])

    if i==0:
      if key=="LIB       " or\
         key=="REQUEST   " or\
         key=="BACKUP    " or\
         key=="MASTER    ":
        inp_typ="LIB"
      elif key=="TRANS     ":
        inp_typ="TRA"
      elif key=="ENTRY     ":
        inp_typ="ENT"
      elif key=="DICTION   ":
        inp_typ="DIC"
      else:
        msg="The first record must be LIB, REQUEST, BACKUP, MASTER, TRANS, ENTRY or DICTION."
        print_error_fatal(msg,line)

    if key=="LIB       " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="LIB       "

    elif key=="REQUEST   " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="REQUEST   "

    elif key=="BACKUP    " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="BACKUP    "

    elif key=="MASTER    " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="MASTER    "

    elif key=="TRANS     " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="TRANS     "

    elif key=="ENDLIB    " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="ENDLIB    "

    elif key=="ENDREQUEST" and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="ENDREQUEST"

    elif key=="ENDBACKUP " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="ENDBACKUP "

    elif key=="ENDMASTER " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="ENDMASTER "

    elif key=="ENDTRANS  " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="ENDTRANS  "

    elif (key=="ENTRY     " and sec!="DIC") or key=="DICTION   ":
      if inp_typ!="ENT" and inp_typ!="DIC":
        check_sysid(key,sysid,san,line)
      if key=="DICTION   ":
        sysid="DICTION   "
      else:
        sysid="ENTRY     "
      san=""
      sec=""
      an=line[17:22]
      nan+=1
      isan=0
      print("counting ... "+an)

    elif (key=="ENDENTRY  " and sec!="DIC") or key=="ENDDICTION":
      check_sysid(key,sysid,san,line)
      if key=="ENDDICTION":
        sysid="ENDDICTION"
      else:
        sysid="ENDENTRY  "
      nsan[an]=isan

    elif (key=="SUBENT    " and sec!="DIC") or key=="SUBDICT   ":
      check_sysid(key,sysid,san,line)
      if key=="SUBDICT   ":
        sysid="SUBDICT   "
        sec="DIC"
      else:
        sysid="SUBENT    "
      irec=0
      san=line[14:22]
      isan+=1
      print("counting ... "+an+"."+san[5:8])

    elif key=="NOSUBENT  " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="NOSUBENT  "
      san=line[14:22]
      isan+=1
      print("counting ... "+an+"."+san[5:8])

    elif (key=="ENDSUBENT " and sec!="DIC") or key=="ENDSUBDICT":
      check_sysid(key,sysid,san,line)
      if key=="ENDSUBDICT":
        sec=""
        sysid="ENDSUBDICT"
      else:
        sysid="ENDSUBENT "
      nrec[san]=irec
      if re.compile("001$").search(san): # common (001) subentry
        ndat[san]=0
        mdat[san]=0
        nlin[san]=0

    elif key=="BIB       " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="BIB       "
      irec+=1
      sec="BIB"
      ibib=0
      ikey=0

    elif key=="ENDBIB    " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="ENDBIB    "
      irec+=1
      sec=""
      nbib[san]=ibib
      nkey[san]=ikey

    elif key=="NOBIB     " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="NOBIB     "
      irec+=1
      sec=""
      nbib[san]=0

    elif key=="COMMON    " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="COMMON    "
      irec+=1
      sec="COM"
      icom=0
      ifld=0

    elif key=="ENDCOMMON " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="ENDCOMMON "
      irec+=1
      sec=""
      ncom[san]=icom
      mcom[san]=int(ifld/2)

    elif key=="NOCOMMON  " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="NOCOMMON  "
      irec+=1
      sec=""
      ncom[san]=0
      mcom[san]=0

    elif key=="DATA      " and sec!="DIC" and sec!="DAT":
      check_sysid(key,sysid,san,line)
      sysid="DATA      "
      irec+=1
      sec="DAT"
      idat=0
      ifld=0

    elif key=="ENDDATA   " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="ENDDATA   "
      irec+=1
      sec=""
      ndat[san]=idat
      mdat[san]=int(ifld/2)
      n=int((mdat[san]+5)/6)
      if ((ndat[san]-n*2)%n!=0):
        msg="The number of the data records incorrect."
        print_error_fatal(msg,line)
      else:
        nlin[san]=int((ndat[san]-n*2)/n)

    elif key=="NODATA    " and sec!="DIC":
      check_sysid(key,sysid,san,line)
      sysid="NODATA    "
      irec+=1
      sec=""
      ndat[san]=0
      mdat[san]=0

    elif sec!="BIB" and sec!="COM" and sec!="DAT" and sec!="DIC":
      msg="Unexpected system identifier found"
      print_error_fatal(msg,line)

    else: 
      irec+=1

      if sec=="BIB":
        ibib+=1 
        if re.compile(r"\S").search(key):
          ikey+=1

      elif sec=="COM" or sec=="DAT":
        if re.compile(r"\.").search(line): # data line with number
          pass

        elif re.compile(r"\S").search(line): # heading or unit
          for i in range(6):
            col1=11*i
            col2=col1+11
            char=line[col1:col2]
            if re.compile(r"\S").search(char):
              ifld+=1

        else: # data line without number
          pass
          
        if sec=="COM":
          icom+=1 
        elif sec=="DAT":
          idat+=1 

  return nan


def check_sysid(key,sysid,san,line):
  status=False
  if key=="LIB       " or  key=="REQUEST   "\
  or key=="BACKUP    " or  key=="MASTER    "\
  or key=="TRANS     ":
    if sysid=="          ":
      status=True
  elif key=="ENDLIB    " or key=="ENDREQUEST"\
    or key=="ENDBACKUP " or key=="ENDMASTER "\
    or key=="ENDTRANS  ":
    if sysid=="ENDENTRY  " or sysid=="ENDDICTION":
      status=True

  elif key=="ENTRY     " or key=="DICTION   ":
    if sysid=="LIB       " or sysid=="REQUEST   "\
    or sysid=="BACKUP    " or sysid=="MASTER    "\
    or sysid=="TRANS     "\
    or sysid=="ENDENTRY  " or sysid=="ENDDICTION":
      status=True

  elif key=="ENDENTRY  ":
    if sysid=="ENDSUBENT " or sysid=="NOSUBENT  ":
      status=True

  elif key=="ENDDICTION":
    if sysid=="ENDSUBDICT":
      status=True

  elif key=="SUBENT    " or key=="NOSUBENT  ":
    if sysid=="ENTRY     " or sysid=="ENDSUBENT "\
    or sysid=="NOSUBENT  ":
      status=True

  elif key=="SUBDICT   ":
    if sysid=="DICTION   " or sysid=="ENDSUBDICT":
      status=True

  elif key=="ENDSUBENT ":
    if sysid=="ENDDATA   " or sysid=="NODATA    ":
      status=True
    elif sysid=="ENDCOMMON " or sysid=="NOCOMMON  ":
      if san[5:8]=="001":
        status=True

  elif key=="ENDSUBDICT":
    if sysid=="SUBDICT   ":
      status=True

  elif key=="BIB       " or key=="NOBIB     ":
    if sysid=="SUBENT    ":
      status=True

  elif key=="ENDBIB    ":
    if sysid=="BIB       ":
      status=True

  elif key=="COMMON    " or key=="NOCOMMON  ":
    if sysid=="ENDBIB    " or sysid=="NOBIB     ":
      status=True

  elif key=="ENDCOMMON ":
    if sysid=="COMMON    ":
      status=True

  elif key=="DATA      " or key=="NODATA    ":
    if sysid=="ENDCOMMON " or sysid=="NOCOMMON  ":
      status=True

  elif key=="ENDDATA   ":
    if sysid=="DATA      ":
      status=True

  if not status:
    msg="Unexpected system identifier found after "+sysid+": "+key
    print_error_fatal(msg,line)

  return


def get_args(ver):

  parser=argparse.ArgumentParser(\
   usage="Add EXFOR record identification",\
   epilog="example: x4_seqadd.py -i exfor.txt -o exfor_ord.txt")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-i", "--file_inp",\
   help="input EXFOR file")
  parser.add_argument("-o", "--file_out",\
   help="output EXFOR file")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")
  parser.add_argument("-n", "--no19ad",\
   help="do not add 19 to two-digit year and do not alter N2 of END records", action="store_true")
  parser.add_argument("-d", "--deltid",\
   help="delete the transmission ID in N6", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("SEQADD (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force
  no19ad0=args.no19ad
  deltid0=args.deltid

  file_inp=args.file_inp
  if file_inp is None:
    file_inp=input("input EXFOR file [exfor.txt] -------> ")
    if file_inp=="":
      file_inp="exfor.txt"
  if not os.path.exists(file_inp):
    print(" ** File "+file_inp+" does not exist.")
  while not os.path.exists(file_inp):
    file_inp=input("input EXFOR file [exfor.txt] -------> ")
    if file_inp=="":
      file_inp="exfor.txt"
    if not os.path.exists(file_inp):
      print(" ** File "+file_inp+" does not exist.")

  file_out=args.file_out
  if file_out is None:
    file_out=input("output EXFOR file [exfor_ord.txt] --> ")
  if file_out=="":
    file_out="exfor_ord.txt"
  if os.path.isfile(file_out):
    msg="File '"+file_out+"' exists and must be overwritten."
    print_error(msg,"",force0)

  return file_inp,file_out,force0,no19ad0,deltid0


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
  seqadd()
  exit()
