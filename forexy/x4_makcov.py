#!/usr/bin/python3
ver="2026.06.24"
############################################################
# MAKCOV Ver.2026.06.24
# (Utility to convert EXFOR in JSON to covariance)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
############################################################
#
# This combinations with MAKJSO v.20240820 reproduces 
#  sok_plt.txt and fort.12 of np237-20240823!
#
# Remark on setting of heading (hed) files.
#
# When the total uncertainty heading is given with U (F),
#  headings of all partial uncertainties are expected to
#  be defined with 1 (0).
#
# Note on shape flag "S" at 1st column of heading file
#
# S combined with/orrelation flag 1:
#   - The total unc. heading may be present with "U", or absent.
#   - When the dataset is not treated as shape
#     . this unc. is kept in (or added to) the total unc.
#     . this unc. is used for correlation estimation.
#   - When the dataset is treated as shape
#     . this unc. is subtracted from (or not added to ) the total unc..
#     . this unc. is not used for correlation estimation.
#
# S combined with correlation flag -:
#   - The total unc. heading must be present with "F".
#   - When the dataset is not treated as shape
#     . this unc. is not used in any operation
#   - When the dataset is treated as shape
#     . this unc. is subtracted from the total unc..
#     . this unc. is also subtract not included in the correlated unc..
#
#====================================
#Example of S with 1
#
# 1. When treated as absolute
# Total: ERR-T
# Unc  : ERR-T - ERR-1 - MONIT-ERR
# Cor  : ERR-1 + MONIT-ERR
#
# 2. When treated as shape
# Total: ERR-T - MONIT-ERR
# Unc  : ERR-T - ERR-1 - MONIT-ERR
# Cor  : ERR-1
#---
# ERR-T     U
# ERR-1     1
#SMONIT-ERR 1
#====================================
#Example of S with -
#
# 1. When treated as absolute
# Total: ERR-T
# Unc  : ERR-S
# Cor  : ERR-T - ERR-S
#
# 2. When treated as shape
# Total: ERR-T - MONIT-ERR
# Unc  : ERR-S
# Cor  : ERR-T - ERR-S - MONIT-ERR
#---
# ERR-T     F
# ERR-S     0
#SMONIT-ERR -
#====================================
#Example of absence of total uncertainty
#
# 1. When treated as absolute
# Total: ERR-1 + ERR-2 + ERR-3
# Unc  : ERR-1
# Cor  : ERR-2 + ERR-3
#
# 2. When treated as shape
# Total: ERR-1 + ERR-2
# Unc  : ERR-1
# Cor  : ERR-2
#---
#
# ERR-1     0
# ERR-2     1
#SERR-3     1
######################################################
# Argument for heads, inds, vals, unis, facs
#  0: x_low (must be present)
#  1: x_hig (must be present)
#  2: dx
#  3: y (must be present)
#  4: y_ref
#  5: dy_tot
#  6: dy_1 (1st partial)
#  7: dy_2 (2nd partial)
#  ...
#
# Argument for typs, flgs and cors
#  0: y_err(tot)
#  1: y_err(1st) 
#  2: y_err(2nd)
#  ...
#
# Values given by find_head_1 and find_head_2
#  (e.g., $heading=EN, $unit=KEV, $column=1)
#
#         COMMON       ERR-ANALYS        DATA
# heads[] $heading     $heading          $heading
# inds[ ] None         None              $column
# unis[ ] $unit        PER-CENT          $unit
# vals[ ] $value       $value            None
#
# heads=[]
# inds=[] # column position of the heading (for DATA section)
# unis=[] # unit for the heading
# facs=[] # factor for conversion to base unit (e.g., MeV -> eV)
# vals=[] # value for the heading (for COMMON section and ERR-ANALYS)
# flgs=[] # shape operation flag  for uncertainty heading (" " or "S")
# cors=[] # correlation property for uncertainty heading
#         #                          ("U", "F", "0", "1",  "-" or "*")
# typs=[] # MU if lower uncertainty boundary is adopted

import argparse
import datetime
import json
import math
import os
import re
import time

def makcov():
  args=get_args(ver)
  main(*get_input(args))

def main(file_j4,file_hed,file_dict,data_id,file_cov,file_log,x_min,x_max,force0,shape0,outfrc0):
  time_start=time.time()

  global x4_json
  global dict_json

  force=force0
  shape=shape0
  outfrc=outfrc0

  x4_json_full=read_x4json(file_j4)

  if x4_json_full["title"]!="J4 - EXFOR in JSON without pointer without common subentry":
    msg="The input JSON EXFOR file must be the one processed by POIPOI without option -c."
    print_error_fatal(msg,x4_json_full["title"])
  
  dict_json=read_dict(file_dict)

  an=data_id[0:5]
  san=data_id[6:9]
  if len(data_id)==11:
    pointer=data_id[10:11]
  else:
    pointer=""
  ansan=an+san

  if x4_json_full["entries"][0]["ENTRY"]["N1"]!=an:
    msg="Entry "+an+" does not exist in "+file_j4
    print_error_fatal(msg,"")
  elif x4_json_full["entries"][0]["subentries"][0]["SUBENT"]["N1"]!=ansan:
    msg="Subentry "+san+" does not exist in "+file_j4
    print_error_fatal(msg,"")
  elif "REACTION" not in x4_json_full["entries"][0]["subentries"][0]:
    msg="REACTION does not exist for subentry "+an+"."+san+" in "+file_j4
    print_error_fatal(msg,"")
  elif x4_json_full["entries"][0]["subentries"][0]["REACTION"][0]["pointer"]!=pointer:
    if pointer=="":
      msg="Pointer must be specified for Subentry "+an+"."+san+" in "+file_j4
    else:
      msg="Pointer "+pointer+" does not exist for Subentry "+an+"."+san+" in "+file_j4
    print_error_fatal(msg,"")
  else:
    x4_json=x4_json_full["entries"][0]["subentries"][0]

  (author,year,institute)=print_log_1(file_log,an,san,pointer,shape)
  (heads,inds,unis,facs,vals,flgs,cors,typs,txts)=read_x4head(file_hed,shape,file_log)

# get values in COMMON section and ERR-ANALYS in the data subentry
  (unis,vals,typs)=find_head_1(an,ansan,pointer,heads,unis,vals,typs)

# get column positions in DATA section
  (inds,unis)=find_head_2(an,ansan,pointer,heads,inds,unis)

  for j, head in enumerate(heads):
    if re.compile(r"\S").search(head) and unis[j] is None:
      msg="Heading "+head+" is specified in "+file_hed+", but missing in "+file_j4+"."
      print_error_fatal(msg,"")


# get conversion factors
  facs=get_convfac(heads,unis,facs)

# get base unit
  (x_uni,y_uni)=get_baseuni(unis)

  x=[]
  dx=[]
  y=[]
  dy=[]
  nheads=len(heads)

  nskip=0
  nrej_low=0
  nrej_hig=0
  for i, data_line in enumerate(x4_json["DATA"]["value"]):
    if "flag" in x4_json["DATA"]: 
      if "#" in x4_json["DATA"]["flag"][i]: # data line flagged by #
        nskip+=1
        continue
    (x0,dx0,y0,dy0)=make_table(nheads,data_line,heads,inds,unis,facs,vals,flgs,cors,x_min,x_max,shape)
    if y0 is None:
      if x0<x_min:
        nrej_low+=1
      elif x0>x_max:
        nrej_hig+=1
        
    else:
      x.append(x0)
      dx.append(dx0)
      y.append(y0)
      dy.append(dy0)

  if heads[5]!="" and cors[0]!="*" and cors[0]!="+": # residual uncertainty is added
    if cors[0]=="U":
      cors.append(0.)
    elif cors[0]=="F":
      cors.append(1.)
    heads.append("ERR-R")
    flgs.append(" ")

  (dymin,dymax)=print_table(file_cov,an,san,pointer,x,dx,y,dy,cors,x_uni,y_uni,author,year,institute,shape,outfrc)

  print_log_2(file_log,an,san,pointer,year,author,x,dy,heads,flgs,cors,typs,txts,dymin,dymax,shape,nskip,nrej_low,nrej_hig)

  time_end=time.time()
  time_elapsed=format(time_end-time_start, ".2f")
  print("MAKCOV: Processing terminated normally. "+time_elapsed+" sec.\n")


def get_baseuni(unis):
  ind=get_index("025",unis[0])
  x_fam=dict_json["025"][ind]["unit_family_code"]
  if x_fam=="E":
    x_uni="eV"
  elif x_fam=="A":
    x_uni="deg"
  else:
    msg="Base unit of the unit family "+x_fam+" is unknown."
    print_error_fatal(msg,"")

  ind=get_index("025",unis[3])
  y_fam=dict_json["025"][ind]["unit_family_code"]
  if y_fam=="B":
    y_uni="b"
  elif y_fam=="DA":
    y_uni="mb/sr"
  elif y_fam=="NO":
    y_uni="no.dim."
  else:
    msg="Base unit of the unit family "+y_fam+" is unknown."
    print_error_fatal(msg,"")

  return x_uni, y_uni


def get_convfac(heads,unis,facs):
  for i, head in enumerate(heads):
    if unis[i] is not None:
      ind=get_index("025",unis[i])
      if ind==-10:
        msg=unis[i]+" is not defined in Dictionary 25."
        print_error_fatal(msg,"")
      facs[i]=dict_json["025"][ind]["conversion_factor"]
      if head is not None:
        if head=="EN-RSL" or head=="EN-RSL-FW":
          facs[i]=facs[i]*0.5 # full width -> half width

  return facs


def make_table(nheads,data_line,heads,inds,unis,facs,vals,flgs,cors,x_min,x_max,shape):
  val=[0]*nheads
  for i in range(nheads):
    ind=inds[i]
    if ind is None: # value is in COMMON or ERR-ANALYS
      val[i]=vals[i]
    else:
      if data_line[ind] is None: # empty data field
        val[i]=0
      else:
        val[i]=data_line[ind]

    if val[i] is not None:
      val[i]=val[i]*facs[i]

    if i==2:  # dx
      if re.compile(r"\S").search(heads[i]) and unis[i]=="PER-CENT":
        val[i]=val[i]*(val[0]+val[1])/2*0.01
    elif i>4: # dy_1, dy_2, ...
      if re.compile(r"\S").search(heads[i]) and unis[i]!="PER-CENT":
        if heads[i]=="ERR-T"   or heads[i]=="ERR-S" or\
           heads[i]=="ERR-SYS" or heads[i]=="DATA-ERR":
          val[i]=val[i]/val[3]*100. # conversion to % uncertainty
        elif re.compile(r"ERR\-\d{1,2}").search(heads[i]):
          val[i]=val[i]/val[3]*100. # conversion to % uncertainty
        elif heads[i]=="MONIT-ERR":
          val[i]=val[i]/val[4]*100. # conversion to % uncertainty
        else:
          msg=heads[i]+": This partial unc. heading cannot be processed."
          print_error_fatal(msg,"")

# obtain x
  x=(val[0]+val[1])/2

  if x<x_min or x>x_max:
    dx=None
    y=None
    dy=None
    return x,dx,y,dy

# obtain dx
  if val[2] is None:
    dx=(val[1]-val[0])/2
  else:
    if val[2]>(val[1]-val[0])/2:
      dx=val[2]
    else:
      dx=(val[1]-val[0])/2

# obtain y
  y=val[3]

# obtain total uncertainty dy[0]
  dy=[]
  if val[5] is None: # total uncertainty must be calculated
    dysum2=0
    for i in range(6,nheads):
      j=i-5
      if shape and flgs[j]=="S":
        continue
      else:
        dysum2=dysum2+val[i]**2 
    dyt=math.sqrt(dysum2)
  else: # total uncertainty is in EXFOR
    if shape:
      dysum2=0
      for i in range(6,nheads):
        j=i-5
        if flgs[j]=="S":
          dysum2=dysum2+val[i]**2
      if val[5]**2 < dysum2:
        msg="quadrature sum > total uncertainty: x_min="+x[0]+", x_max="+x[1]
        print_error_fatal(msg,"")
      else:
        dyt=math.sqrt(val[5]**2-dysum2)
    else:
      dyt=val[5]

  dy.append(dyt)
    

# obtain partial uncertainties dy[1], dy[2], ...
  for i in range(6,nheads):
    j=i-5
    if cors[0] is None: # this partial uncertainty can be correlated or uncorrelated one
      if shape and flgs[j]=="S":
        dy.append(0)
      else:
        dy.append(val[i])
    elif cors[0]=="U": # this partial uncertainty has correlation flag 1
      if shape and flgs[j]=="S":
        dy.append(0)
      else:
        dy.append(val[i])
    elif cors[0]=="F": # this partial uncertainty has correlation flag 0 or -
      if cors[j]=="-":
        dy.append(0)
      else:
        dy.append(val[i])

# residual uncertainty (when total uncertainty in EXFOR)
  if val[5] is not None:
    dysum2=0
    for i, dyp in enumerate(dy):
      if i==0:
        continue
      else:
        dysum2=dysum2+dyp**2

    if dyt**2 < dysum2:
      msg="quadrature sum > total uncertainty: x_min="+str(val[0])+", x_max="+str(val[1])
      print_error_fatal(msg,"")
    else:
      dy_res=math.sqrt(dyt**2-dysum2)
      dy.append(dy_res)

  return x,dx,y,dy


def print_log_1(file_log,an,san,pointer,shape):
  f=open(file_log,"w")

  line="*"+an+"."+san
  if re.compile(r"\S").search(pointer):
    line+="."+pointer
  else:
    line+="  "
  line+=" "+str(x4_json["SUBENT"]["N2"])

  institute=None
  if "FACILITY" in x4_json:
    for bib_text in x4_json["FACILITY"]:
      if bib_text["coded_information"]["institute"] is not None:
        institute=bib_text["coded_information"]["institute"]
        break
  if institute is None:
    institute="???????"
    line+=" "+institute
  else:
    line+=" "+ bib_text["coded_information"]["institute"]

  author=None
  if "STATUS" in x4_json:
    for bib_text in x4_json["STATUS"]:
      if bib_text["coded_information"] is not None:
        if bib_text["coded_information"]["author"] is not None:
          author=bib_text["coded_information"]["author"]
          line+=" "+author
          date=bib_text["coded_information"]["reference"]["field"]["date"]
          year=str(date)[0:4]
          line+=","+year

  if author is None:
    if "AUTHOR" in x4_json:
      for bib_text in x4_json["AUTHOR"]:
        if bib_text["coded_information"] is not None:
          authors=bib_text["coded_information"]
          author=authors[0]
          if len(authors)!=1:
            author=author+"+" 
          break
   
    if "REFERENCE" in x4_json:
      for bib_text in x4_json["REFERENCE"]:
        if bib_text["coded_information"] is not None:
          date=x4_json["REFERENCE"][0]["coded_information"]["code_unit"][0]["field"]["date"]
          year=str(date)[0:4]
          break

  f.write(line+" ")

  f.close()
  return author, year, institute


def print_log_2(file_log,an,san,pointer,year,author,x,dy,heads,flgs,cors,typs,txts,dymin,dymax,shape,nskip,nrej_low,nrej_hig):
  f=open(file_log,"a")

  minx="%7.1E" % min(x)
  maxx="%7.1E" % max(x)
  line=minx+" "+maxx+" "+year+" "+author
  f.write(line+"\n")

  if shape:
    f.write("** Treated as a shape dataset.\n")


  npoints="%5s" % str(len(x)+nskip+nrej_low+nrej_hig)
  line="*    "+npoints+" points in JSON EXFOR file"
  f.write(line+"\n")

  nskip="%5s" % nskip
  nrej_low="%5s" % nrej_low
  nrej_hig="%5s" % nrej_hig
  line="*    "+nskip+" points flagged by # skipped"
  f.write(line+"\n")
  line="*    "+nrej_low+" points below lower boundary skipped"
  f.write(line+"\n")
  line="*    "+nrej_hig+" points above upper boundary skipped"
  f.write(line+"\n")

  for i in range(len(cors)):
    dymin[i]="%3.1f" % dymin[i]
    dymin[i]="%4s" % dymin[i]
    dymax[i]="%3.1f" % dymax[i]
    dymax[i]="%4s" % dymax[i]

  for i in range(5,len(heads)):
    j=i-5
    line="%2s" % str(j)
    line=""
    if flgs[j]=="S":
      headout="%-10s" % heads[i]
      if shape:
        line+=headout+":--:---:-----:-----:This uncertainty excluded (due to shape treatment)"
        f.write(line+"\n")
        continue
      elif cors[j]=="-":
        line+=headout+":--:---:-----:-----:This uncertainty ignored (only for subtraction in shape treatment)"
        f.write(line+"\n")
        continue

    ind=get_index("024",heads[i])

    if j==0 and heads[i]=="":
      line+="ERR-C     :CT:   "
    elif heads[i]=="ERR-R":
      line+="ERR-R     :RU:"+str(cors[j])
    elif ind==-10:
      headout="%-10s" % heads[i]
      line+=""+headout+":AU:"+str(cors[j])
    else:
      headout="%-10s" % heads[i]
      if j==0:
        line+=""+headout+":"+typs[j]+":   "
      else:
        line+=""+headout+":"+typs[j]+":"+str(cors[j])

    if heads[i]=="ERR-R":
      line+=":"+dymin[-1]+"%:"+dymax[-1]+"%"
    else:
      line+=":"+dymin[j]+"%:"+dymax[j]+"%"

    free_text=""
    if j==0 and heads[i]=="":
      free_text="Total uncertainty (calculated)"
    elif heads[i]=="ERR-R":
      if cors[j]==0:
        free_text="Residual uncertainty (specified as uncorrelated)"
      elif cors[j]==1:
        free_text="Residual uncertainty (specified as fully correlated)"
    elif ind==-10:
      free_text=txts[j]
    else:
      if "ERR-ANALYS" in x4_json:
        for bib_text in x4_json["ERR-ANALYS"]:
          if bib_text["coded_information"] is not None:
            if bib_text["coded_information"]["heading"]==heads[i]:
              free_text="\n".join(bib_text["free_text"])
              if re.compile(r"\S").search(free_text):
                free_text=re.sub(r"^\s+|\s+$", "",free_text)
                free_text=re.sub(r"\s{2,}", " ",free_text)
                free_text=re.sub("\n", " ",free_text)
              break
      
      if free_text=="":
        free_text="!!! Heading is not explained under ERR-ANALYS"

    line+=":"+free_text

    f.write(line+"\n")

  f.write("\n")
  f.close()
  return

def print_table(file_cov,an,san,pointer,x,dx,y,dy,cors,x_uni,y_uni,author,year,institute,shape,outfrc):
  dymin=[100]*len(cors)
  dymax=[0]*len(cors)

  f=open(file_cov,"w")

  line="#"+an+"."+san
  if pointer!="":
    line+="."+pointer
  else:
    line+="  "

  line+=" "+author+","+year

  line="%-44s" % line
  f.write(line+"\n")

  line="#"+str(x4_json["SUBENT"]["N2"])+"    "+institute+" "
  line="%-38s" % line
  npoints="%6s" % len(x)
  f.write(line+npoints+"\n")

  if outfrc:
    line="#x          dx         y          dy/y      "
  else:
    line="#x          dx         y          dy        "

  f.write(line+"\n")

  line="#"
  line+="{:<11s}".format(x_uni)
  line+="{:<11s}".format(x_uni)
  line+="{:<11s}".format(y_uni)
  if outfrc:
    line+="{:<11s}".format("no.dim.")
  else:
    line+="{:<11s}".format(y_uni)
  f.write(line+"\n")

  for i in range (len(x)):
    line=""
    line+="{:>11.4E}".format(x[i])
    line+="{:>11.4E}".format(dx[i])
    line+="{:>11.4E}".format(y[i])
    if outfrc:
      line+="{:>11.4E}".format(dy[i][0]/100.)
    else:
      line+="{:>11.4E}".format(dy[i][0]*y[i]*0.01)
    f.write(line+"\n")

    if (dy[i][0]<dymin[0]):
      dymin[0]=dy[i][0]
    if (dy[i][0]>dymax[0]):
      dymax[0]=dy[i][0]

  f.write("\n")

  if cors[0]=="*":
    f.write("#* cor(x,y) estimation skipped since the total uncertainty heading is flagged by *.\n")

  elif cors[0]=="+":
    f.write("#+ cor(x,y) estimation skipped since the total uncertainty heading is flagged by +.\n")

  else:
    if shape:
      f.write("# cor(x,y) estimated with shape dataset treatment\n")
    else:
      f.write("# cor(x,y) estimated with absolute dataset treatment\n")

    for i in range (len(x)):
      line=""
      nout=0
      for j in range (i+1):
        cov=0.
        for k in range(1,len(cors)):

          if (dy[i][k]<dymin[k]):
            dymin[k]=dy[i][k]
          if (dy[i][k]>dymax[k]):
            dymax[k]=dy[i][k]

          if dy[i][k]==0 or dy[j][k]==0: # maybe partial uncertainties skipped
            continue
          if (i==j):
            cov=cov+dy[i][k]*dy[j][k]
          else:
            cov=cov+dy[i][k]*dy[j][k]*cors[k]
        cor=cov/dy[i][0]/dy[j][0]
        line=line+"{:>6.3f}".format(cor)
        nout+=1
        if nout==12 and j!=i:
          f.write(line+"\n")
          line=""
          nout=0
      f.write(line+"\n")

  f.close()
  return dymin,dymax


def read_x4json(file_j4):
  f=open(file_j4)
  try:
    x4_json=json.load(f)
  except json.JSONDecodeError:
    msg=file_j4+" is not in JSON format."
    print_error_fatal(msg,"")

  if not re.compile("^J4 - EXFOR in JSON").search(x4_json["title"]):
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

  f.close()
  return dict_json


def read_x4head(file_hed,shape,file_log):
  f=open(file_log,"a")
  heads=[]
  inds=[]
  unis=[]
  facs=[]
  vals=[]
  flgs=[]
  cors=[]
  typs=[]
  txts=[]
  lines=get_file_lines(file_hed)

  for i, line in reversed(list(enumerate((lines)))):
    if i>5 and line[0:1]=="#":
      del(lines[i]) # removal of commented out partial uncertainty headings

  for i, line in enumerate(lines): # check flag at the 1st column of heading file
    if not re.compile(r"\S").search(line): # empty line
      continue
    elif re.compile("^s").search(line): # old heading file
      msg=file_hed+": Flag s is obsolete. Replaced with S."
      print_error_1(msg,line)
      line=re.sub("^s", "S",line) # to support old heading file
    if i==0 or i==1 or i==3: # headings for xmin, xmax, y
      if line[0:1]!=" ":
        msg=file_hed+": Flag"+line[0:1]+" is illegal. Must be blank."
        print_error_fatal(msg,line)
    elif i==2 or i==4 or i==5: # heading for dx, y_ref or dy_tot
      if line[0:1]=="#":
        lines[i]=""
      elif line[0:1]!=" ":
        msg=file_hed+": Flag "+line[0:1]+"  is illegal. Only # is allowed."
        print_error_fatal(msg,line)
 #  else: # headings for partial uncertianties dy1, dy2, ...
 #    if line[0:1]=="#":
 #      lines.pop(i)  #  partial uncertainty heading line deleted from the array
      elif line[0:1]!=" " and line[0:1]!="S":
        msg=file_hed+": Flag "+line[0:1]+"  is illegal. Only # or S is allowed."
        print_error_fatal(msg,line)

  for i, line in enumerate(lines):
    m=re.compile("#.+$").search(line)
    if m is not None:
      txt=m.group()
    else:
      txt=""
    line=re.sub(r"\s+$", "",line)
    line=re.sub(r"\s*\#.+$", "",line)
    line=re.sub("^s", "S",line) # to support old heading file

    heads.append("")
    inds.append(None)
    unis.append(None)
    vals.append(None)
    facs.append(None)

    if not re.compile(r"\S").search(line): # empty line
      if (i==0):
        msg=file_hed+": independent variable minimum (x_low) heading missing"
        print_error_fatal(msg,"")
      elif (i==1):
        msg=file_hed+": independent variable maximum (x_hig) heading missing"
        print_error_fatal(msg,"")
      elif (i==3):
        msg=file_hed+": qunatity measured (y) heading missing"
        print_error_fatal(msg,"")
      elif (i==5):
        flgs.append(None)
        cors.append(None)
        typs.append("  ")
        txts.append("")
    else:
      arr=re.split(r"\s+",line[1:])
      heads[i]=arr[0]
      if i<5:    # xmin, xmax, dx, y, yref
        if len(arr)>1:
          msg=arr[0]+": One element (heading) expected."
          print_error_fatal(msg,line)
        if i==3 and arr[0]!="DATA":
          msg=arr[0]+": Unusual heading for the quantity measured."
          f.write("** "+msg+"\n")
        if i==4 and not re.compile("MONIT").search(arr[0]):
          msg=arr[0]+": Unusual heading for the reference quantity measured."
          f.write("** "+msg+"\n")

      elif i==5: # dy_tot
        if arr[0]!="ERR-T" and arr[0]!="DATA-ERR" and arr[0]!=" ":
          msg=arr[0]+": Unusual heading for total uncertainty."
          f.write("** "+msg+"\n")
        if len(arr)!=2:
          msg=arr[0]+": Two elements (heading, residual correlation) expected."
          print_error_fatal(msg,line)
        if (arr[1]!="U" and arr[1]!="F" and arr[1]!="*" and arr[1]!="+"):
          msg=arr[0]+": Residual correlation flag must be U, F, * or +."
          print_error_fatal(msg,line)
        flgs.append(None)
        cors.append(arr[1]) # U, F, * or +
        if arr[1]=="*":
          typs.append("* ")
        elif arr[1]=="+":
          typs.append("+ ")
        else:
          typs.append("  ")
        txts.append("")

      else:      # partial uncertainty (dy_1, dy_2, ...)
        if arr[0]=="ERR-T":
          msg=arr[0]+": Unusual heading for a partial uncertainty."
          f.write("** "+msg+"\n")
        if len(arr)<2:
          msg=arr[0]+": Minimum two elements expected."
          print_error_fatal(msg,"")
        elif len(arr)>4:
          msg=arr[0]+": Maximum three elements expected."
          print_error_fatal(msg,"")
        else:
          if len(arr)==3: # constant uncertainty given by user
            unis[i]="PER-CENT"
            vals[i]=float(arr[2])

        if cors[0]=="*":
          msg=arr[0]+": This line is should not exist since "+heads[5]+" is defined with * or +"
          print_error_fatal(msg,line)
        elif cors[0]=="+" and float(arr[1])!=0:
          msg=arr[0]+": Flag 0 must be used when estimation of the correlation coefficient is not required."
          print_error_fatal(msg,line)

        if arr[1]=="-":
          if line[0:1]!="S":
            msg=arr[0]+": Flag - must be used with flag S on the first column"
            print_error_fatal(msg,line)
          if cors[0]!="F":
            msg=arr[0]+": Flag - must be used with flag F for the total uncertainty heading"
            print_error_fatal(msg,line)
        else:
          try:
            arr[1]=float(arr[1])
          except Exception:
            msg=arr[0]+": Correlation flag must be -, 0 or 1"
            print_error_fatal(msg,line)

          if arr[1]==0 or arr[1]==1: # correlation flag must be 1 (0) if the residual flag is U (F)
            if cors[0]=="U" and arr[1]!=1:
              msg=arr[0]+": Correlation 1 expected since "+heads[5]+" is defined with U."
              print_error_fatal(msg,"")
            elif cors[0]=="F" and arr[1]!=0:
              msg=arr[0]+": Correlation 0 expected since "+heads[5]+" is defined with F."
              print_error_fatal(msg,"")
            elif cors[0]=="+" and arr[1]!=0:
              msg=arr[0]+": Correlation 0 expected since "+heads[5]+" is defined with +."
              print_error_fatal(msg,"")
          else:
            msg=arr[0]+": Correlation must be -, 0 or 1 for a partial uncertainty heading."
            print_error_fatal(msg,"")

        if line[0:1]=="S": # S must be used with correlation flag 1 (with residual flag U) or -.
          if arr[1]!="-" and float(arr[1])!=1 and cors[0]!="+":
            msg=arr[0]+": Flag S must be used with flag 1 or - on the same line"
            print_error_fatal(msg,line)
          elif arr[1]==1 and cors[0]!="U" and re.compile(r"\S").search(heads[5]):
            msg=arr[0]+": Flag S combined with flag 1 cannot be with the flag "+cors[0]+" under "+heads[5]
            print_error_fatal(msg,line)

        flgs.append(line[0:1])
        cors.append(arr[1]) # 0 or 1 or -
        typs.append("  ")
        ind=get_index("024",arr[0])
        if ind==-10:
          txts.append(txt)
        else:
          txts.append("")

  f.close()
  return heads,inds,unis,facs,vals,flgs,cors,typs,txts


def find_head_1(an,ansan,pointer,heads,unis,vals,typs):
  if "ERR-ANALYS" in x4_json:
    for bib_text in x4_json["ERR-ANALYS"]:
      for i, head in enumerate(heads):
        if bib_text["coded_information"] is None:
          continue
        if bib_text["coded_information"]["heading"]==head:
          if bib_text["coded_information"]["minimum_value"] is not None:
            vals[i]=bib_text["coded_information"]["minimum_value"]
            unis[i]="PER-CENT"
            j=i-5
            typs[j]="MU"
            break

  if "COMMON" in x4_json:
    headings=x4_json["COMMON"]["heading"]
    for i, heading in enumerate(headings):
      if x4_json["COMMON"]["pointer"][i]!="" and \
         x4_json["COMMON"]["pointer"][i]!=pointer:
        continue
      for j, head in enumerate(heads):
        if heading==head:
          vals[j]=x4_json["COMMON"]["value"][i]
          unis[j]=x4_json["COMMON"]["unit"][i]

  return unis,vals,typs


def find_head_2(an,ansan,pointer,heads,inds,unis):
  headings=x4_json["DATA"]["heading"]
  for i, heading in enumerate(headings):
    if x4_json["DATA"]["pointer"][i]!="" and\
       x4_json["DATA"]["pointer"][i]!=pointer:
      continue
    for j, head in enumerate(heads):
      if (heading==head):
        inds[j]=i
        unis[j]=x4_json["DATA"]["unit"][i]

  return inds, unis


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
   usage="Convert EXFOR in JSON to a tabular format",\
   epilog="example: x4_makcov.py -i exfor.json -j exfor_hed.txt -d dict.json -e 22742.004.1 -o x4_makcov_out.txt -g x4_makcov.log")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-i", "--file_j4",\
   help="input J4 file")
  parser.add_argument("-j", "--file_hed",\
   help="input HED file")
  parser.add_argument("-d", "--file_dict",\
   help="input JSON Dictionary")
  parser.add_argument("-e", "--data_id",\
   help="EXFOR Dataset ID")
  parser.add_argument("-o", "--file_cov",\
   help="output covariance file")
  parser.add_argument("-g", "--file_log",\
   help="output log file (optional)", default="x4_makcov.log")
  parser.add_argument("-l", "--x_min",\
   help="lower boundary of independent variable (optional)")
  parser.add_argument("-u", "--x_max",\
   help="upper boundary of independent variable (optional)")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")
  parser.add_argument("-s", "--shape",\
   help="treat as shape dataset", action="store_true")
  parser.add_argument("-r", "--outfrc",\
   help="print fractional (not absolute) uncertainty", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("MAKCOV (Ver."+ver+") run on "+date)
  print("----------------------------------------")

  force0=args.force
  shape0=args.shape
  outfrc0=args.outfrc

  file_j4=args.file_j4
  if file_j4 is None:
    file_j4=input("input J4 file [exfor.json] -----------------> ")
    if file_j4=="":
      file_j4="exfor.json"
  if not os.path.exists(file_j4):
    print(" ** File "+file_j4+" does not exist.")
  while not os.path.exists(file_j4):
    file_j4=input("input J4 file [exfor.json] -----------------> ")
    if file_j4=="":
      file_j4="exfor.txt"
    if not os.path.exists(file_j4):
      print(" ** File "+file_j4+" does not exist.")

  file_hed=args.file_hed
  if file_hed is None:
    file_hed=input("input HED file [exfor_hed.txt] -------------> ")
    if file_hed=="":
      file_hed="exfor_hed.txt"
  if not os.path.exists(file_hed):
    print(" ** File "+file_hed+" does not exist.")
  while not os.path.exists(file_hed):
    file_hed=input("input HED file [exfor_hed.txt] ------------> ")
    if file_hed=="":
      file_hed="exfor_hed.txt"
    if not os.path.exists(file_hed):
      print(" ** File "+file_hed+" does not exist.")

  file_dict=args.file_dict
  if file_dict is None:
    file_dict=input("input JSON Dictionary [dict.json] ----------> ")
    if file_dict=="":
      file_dict="dict.json"
  if not os.path.exists(file_dict):
    print(" ** File "+file_dict+" does not exist.")
  while not os.path.exists(file_dict):
    file_dict=input("input JSON Dictionary [dict.json] ----------> ")
    if file_dict=="":
      file_dict="dict.json"
    if not os.path.exists(file_dict):
      print(" ** File "+file_dict+" does not exist.")

  data_id=args.data_id
  if data_id is None:
    data_id=input("EXFOR Dataset ID [22742.004.1] -------------> ")
    if data_id=="":
      data_id="22742.004.1"
  data_id=data_id.upper()
  if not re.compile(r"^[1-9A-Z]\d{4}\.\d{3}(\.[1-9A-Z])?$").search(data_id):
    print(" ** EXFOR dataset ID "+data_id+" is illegal.")
  while not re.compile(r"^[1-9A-Z]\d{4}\.\d{3}(\.[1-9A-Z])?$").search(data_id):
    data_id=input("EXFOR Dataset ID [22742.004.1] -------------> ")
    data_id=data_id.upper()
    if data_id=="":
      data_id="22742.004.1"
    if not re.compile(r"^[1-9A-Z]\d{4}\.\d{3}(\.[1-9A-Z])?$").search(data_id):
      print(" ** EXFOR Dataset ID "+data_id+" is illegal.")

  file_cov=args.file_cov
  if file_cov is None:
    file_cov=input("output covariance file [x4_makcov_out.txt] -> ")
  if file_cov=="":
    file_cov="x4_makcov_out.txt"
  if os.path.isfile(file_cov):
    msg="File '"+file_cov+"' exists and must be overwritten."
    print_error(msg,"",force0)

  file_log=args.file_log
# if file_log is None:
#   file_log=input("output log file [x4_makcov.log] ------------> ")
# if file_log=="":
#   file_log="x4_makcov.log"
  print("output log file ----------------------------> "+file_log)
  print("\n")
  if os.path.isfile(file_log):
    msg="File '"+file_log+"' exists and must be overwritten."
    print_error(msg,"",force0)

  x_min=args.x_min
  if x_min is None:
    x_min=-9.9E+20
  else:
    try:
      x_min=float(x_min)
    except Exception:
      print(" ** "+x_min+" is illegal. Specify a real number.")
      while type(x_min)!=float:
        x_min=input("Lower limit of the independent variable [-9.9E+20] ->")
        try:
          x_min=float(x_min)
        except Exception:
          print(" ** "+x_min+" is illegal. Specify a real number.")

  x_max=args.x_max
  if x_max is None:
    x_max=+9.9E+20
  else:
    try:
      x_max=float(x_max)
    except Exception:
      print(" ** "+x_max+" is illegal. Specify a real number.")
      while type(x_max)!=float:
        x_max=input("Upper limit of the independent variable [+9.9E+20] ->")
        try:
          x_max=float(x_max)
        except Exception:
          print(" ** "+x_max+" is illegal. Specify a real number.")

  return file_j4,file_hed,file_dict,data_id,file_cov,file_log,x_min,x_max,force0,shape0,outfrc0


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


def print_error_1(msg,line):
  print("**  "+msg)
  print(line)


def print_error_fatal(msg,line):
  print("**  "+msg)
  print(line)
  exit()


def get_file_lines(file):
  if os.path.exists(file):
    f=open(file, "r")
    lines=f.readlines()
    f.close()
  else:
    msg="File "+file+" does not exist."
    print_error_fatal(msg)
  return lines


if __name__ == "__main__":
  makcov()
  exit()
