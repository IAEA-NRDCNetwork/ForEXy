#!/usr/bin/python3
ver="2026.09.26"
############################################################
# LOTRAN Ver.2026.09.26
# (Utility for Lorentz transformation)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
############################################################
# 
# xxx: inp (input) or out (output)
#
# value
#  value_xxx["A"]: projectile kinetic energy in lab. system
#  value_xxx["E"]: ejectile kinetic energy or excitation energy
#  value_xxx["F"]: ejectile kinetic energy uncertainty
#  value_xxx["G"]: ejectile angle
#  value_xxx["H"]: ejectile angle uncertainty
#  value_xxx["*"]: cross section
#  value_xxx[" "]: cross section uncertainty
#
# frame (=C (centre-of-mass) or L (laboratory))
#  frame_xxx["E"]: frame of ejectile kinetic energy
#  frame_xxx["G"]: frame of ejectile angle
#  frame_xxx["*"]: frame of cross section
#
import argparse
import datetime
import json
import os
import re
import time
import math

ueV   = 931.49410242E+06   # 1 atomic mass unit in eV (AME2020)

def lotran():
  args=get_args(ver)
  main(*get_input(args))


def main(file_dict,file_log,id,ansan,quan,sf1,sf2,sf3,sf4,value_inp,frame_inp,frame_out,force0):
  time_start=time.time()
  global force
  global dict_json
  force=force0

  print("** LOTRAN: Processing "+ansan+" point # "+'{:>5}'.format(str(id+1)))
  dict_json=read_dict(file_dict)

  if quan=="ADX":
    if sf3!="X": # two-body cross section
      (skip,value_out)=transform_adx(id,ansan,sf1,sf2,sf3,sf4,value_inp,frame_inp,frame_out)
    else:
      msg=ansan_out+" point # "+'{:>5}'.format(str(j+1))+": SF3 cannot be X (Must be two-body reaction cross section)"
      print_error_fatal(msg,"")

  elif quan=="DDX":
    if sf3=="X": # inclusive cross section
      (skip,value_out)=transform_ddx(id,ansan,sf1,sf2,sf4,value_inp,frame_inp,frame_out)
    else:
      msg=ansan_out+" point # "+'{:>5}'.format(str(j+1))+": SF3 must be X (Must be inclusive cross section)"
      print_error_fatal(msg,"")

  if file_log!="":
    print_log(file_log,quan,sf1,sf2,sf3,sf4,value_inp,value_out,frame_inp,frame_out)

  time_end=time.time()
  time_elapsed=format(time_end-time_start, ".2f")
  print("LOTRAN: Processing terminated normally. "+time_elapsed+" sec.\n")

  return skip, value_out


def print_log(file_log,quan,sf1,sf2,sf3,sf4,value_inp,value_out,frame_inp,frame_out):
  time_now=datetime.datetime.now()
  time_out=time_now.strftime("%Y-%m-%d %H:%M:%S")
  f=open(file_log,"w")
  f.write("-----------------------------------------------------------------------\n")
  f.write("LOTRAN report "+time_out+"\n")
  f.write("-----------------------------------------------------------------------\n")
  f.write("Target                                          : "+sf1+"\n")
  f.write("Projectile                                      : "+sf2+"\n")
  f.write("Ejectile                                        : "+sf3+"\n")
  f.write("Residual                                        : "+sf4+"\n")
  f.write("Laboratory incident energy (eV)                 : "+str(value_inp["A"])+"\n")
  if quan=="ADX":
    f.write("Residual excitation energy (eV)                 : "+str(value_inp["E"])+"\n")

  if frame_inp["G"]=="L":
    f.write("Input ejectile angle reference system           : lab.\n")
  elif frame_inp["G"]=="C":
    f.write("Input ejectile angle reference system           : c.m.\n")
  if quan=="DDX":
    if frame_inp["E"]=="L":
      f.write("Input ejectile kinetic energy reference system  : lab.\n")
    elif frame_inp["E"]=="C":
      f.write("Input ejectile kinetic energy reference system  : c.m.\n")
  if frame_inp["*"]=="L":
    f.write("Input cross section reference system            : lab.\n")
  elif frame_inp["*"]=="C":
    f.write("Input cross section reference system            : c.m.\n")

  f.write("Input ejectile angle (deg)                      : "+str(value_inp["G"])+"\n")
  if "H" in value_inp:
    f.write("Input ejectile angle uncertainty (deg)          : "+str(value_inp["H"])+"\n")
  if quan=="DDX":
    f.write("Input ejectile kinetic energy (eV)              : "+str(value_inp["E"])+"\n")
    if "F" in value_inp:
      f.write("Input ejectile kinetic energy uncertainty (eV)  : "+str(value_inp["F"])+"\n")
  if quan=="ADX":
    f.write("Input cross section (b/sr)                      : "+str(value_inp["*"])+"\n")
  else:
    f.write("Input cross section (b/sr/eV)                   : "+str(value_inp["*"])+"\n")
  if " " in value_inp:
    if quan=="ADX":
      f.write("Input cross section uncertainty (b/sr)          : "+str(value_inp[" "])+"\n")
    else:
      f.write("Input cross section uncertainty (b/sr/eV)       : "+str(value_inp[" "])+"\n")

  if frame_out["G"]=="L":
    f.write("Output ejectile angle reference system          : lab.\n")
  elif frame_out["G"]=="C":
    f.write("Output ejectile angle reference system          : c.m.\n")
  if quan=="DDX":
    if frame_out["E"]=="L":
      f.write("Output ejectile kinetic energy reference system : lab.\n")
    elif frame_out["E"]=="C":
      f.write("Output ejectile kinetic energy reference system : c.m.\n")
  if frame_out["*"]=="L":
    f.write("Output cross section reference system           : lab.\n")
  elif frame_out["*"]=="C":
    f.write("Output cross section reference system           : c.m.\n")

  for family in value_out:
    if value_out[family]=="NaN":
      f.write("\n!!!! Transformation unsuccesful!! Unphysical input??\n")
      f.write("-----------------------------------------------------------------------\n")
      f.close()
      return
   
  f.write(f"Output ejectile angle (deg)                     : {value_out['G']:.3f}\n")
  if "H" in value_out:
    f.write(f"Output ejectile angle uncertainty (deg)         : {value_out['H']:.3f}\n")
  if quan=="DDX":
    f.write(f"Output ejectile kinetic energy (eV)             : {value_out['E']:.5E}\n")
    if "F" in value_out:
      f.write(f"Output ejectile kinetic energy uncertainty (eV) : {value_out['F']:.5E}\n")
  if quan=="ADX":
    f.write(f"Output cross section (b/sr)                     : {value_out['*']:.5E}\n")
  else:
    f.write(f"Output cross section (b/sr/eV)                  : {value_out['*']:.5E}\n")
  if " " in value_out:
    if quan=="ADX":
      f.write(f"Output cross section uncertainty (b/sr)         : {value_out[' ']:.5E}\n")
    else:
      f.write(f"Output cross section uncertainty (b/sr/eV)      : {value_out[' ']:.5E}\n")

  f.write("-----------------------------------------------------------------------\n")
  f.close()

  return


def transform_adx(id,ansan,sf1,sf2,sf3,sf4,value_inp,frame_inp,frame_out):
  skip=False
  value_out=dict()

  tinc=value_inp["A"]

  if "E" in value_inp:
    eexc=value_inp["E"]
  else:
    eexc=0
  if sf3=="EL" or sf3=="INL" or sf3=="SCT":
    sf3=sf2
    if sf1!=sf4: # SF1 is natural but SF4 is isotopic (wrong coding, CP-D/1164)
      if re.compile(r"^(\d+)\-([A-Z][A-Z]?)\-0$").search(sf1) and\
         re.compile(r"^(\d+)\-([A-Z][A-Z]?)\-\d+$").search(sf4):
        sf1=sf4
  m1=get_atomicweight(sf1)*ueV
  m2=get_atomicweight(sf2)*ueV
  m3=get_atomicweight(sf3)*ueV
  m4=get_atomicweight(sf4)*ueV
  m4=m4+eexc

  (cosh,sinh,invmassq)=get_lorentzfactor(m1,m2,tinc)

  p3cm=tinc_to_pcm(id,ansan,tinc,m1,m2,m3,m4)
  e3cm=math.sqrt(m3**2+p3cm**2)
  if (p3cm/e3cm)*(cosh/sinh) <1:
    msg=ansan+" point # "+'{:>5}'.format(str(id+1))+": v*/beta(cm) < 1"
    print_error(msg,"",True)
    skip=True
    value_out["G"]="NaN"
    value_out["H"]="NaN"
    value_out["*"]="NaN"
    value_out[" "]="NaN"
    return skip,value_out

# transformation of angle (G) and its uncertainty (H)
  if frame_inp["G"]=="L" and frame_out["G"]=="C": # theta(lab) -> theta(cm)
    ang3=value_inp["G"]
    cos3=math.cos(math.radians(ang3))
    (skip,p3,p3cmsq)=anglab_to_plab(id,ansan,m1,m2,m3,m4,ang3,cosh,sinh,invmassq)
    if skip:
      value_out["G"]="NaN"
      value_out["H"]="NaN"
      value_out["*"]="NaN"
      value_out[" "]="NaN"
      return skip,value_out
    ang3cm=anglab_to_angcm(m3,ang3,p3,cosh,sinh)
    value_out["G"]=ang3cm
    if "H" in value_inp: # dtheta(lab) -> dtheta(cm)
      e3=math.sqrt(m3**2+p3**2)
      jacob=abs(p3/(p3*cosh-e3*cos3*sinh)) # J=dtheta(cm)/dtheta(lab)
      value_out["H"]=value_inp["H"]*jacob

  elif frame_inp["G"]=="C" and frame_out["G"]=="L": # theta(cm) -> theta(lab)
    ang3cm=value_inp["G"]
    cos3cm=math.cos(math.radians(ang3cm))
    p3cm=tinc_to_pcm(id,ansan,tinc,m1,m2,m3,m4)
    ang3=angcm_to_anglab(m3,ang3cm,p3cm,cosh,sinh)
    value_out["G"]=ang3
    if "H" in value_inp: # dtheta(cm) -> dtheta(lab)
      (skip,p3,p3cmsq)=anglab_to_plab(id,ansan,m1,m2,m3,m4,ang3,cosh,sinh,invmassq)
      if skip:
        value_out["G"]="NaN"
        value_out["H"]="NaN"
        value_out["*"]="NaN"
        value_out[" "]="NaN"
        return skip,value_out
      e3cm=math.sqrt(m3**2+p3cm**2)
      jacob=abs(p3cm/p3**2*(p3cm*cosh+e3cm*cos3cm*sinh)) # J=dtheta(lab)/dtheta(cm)
      value_out["H"]=value_inp["H"]*jacob

  else:
    value_out["G"]=value_inp["G"]
    if "H" in value_inp:
      value_out["H"]=value_inp["H"]

# transformation of cross section (*) and its uncertainty ( )
  if frame_inp["*"]=="L" and frame_out["*"]=="C": # sig(lab) -> sig(cm)
    if frame_out["G"]=="C":
      ang3cm=value_out["G"]
      cos3cm=math.cos(math.radians(ang3cm))
      p3cm=tinc_to_pcm(id,ansan,tinc,m1,m2,m3,m4)
      ang3=angcm_to_anglab(m3,ang3cm,p3cm,cosh,sinh)
      cos3=math.cos(math.radians(ang3))
    else:
      ang3=value_out["G"]
      cos3=math.cos(math.radians(ang3))

    (skip,p3,p3cmsq)=anglab_to_plab(id,ansan,m1,m2,m3,m4,ang3,cosh,sinh,invmassq)
    if skip:
      value_out["G"]="NaN"
      value_out["H"]="NaN"
      value_out["*"]="NaN"
      value_out[" "]="NaN"
      return skip,value_out
    e3=math.sqrt(m3**2+p3**2)
    jacob=abs((math.sqrt(p3cmsq)/p3**2)*(p3*cosh-e3*cos3*sinh))
    value_out["*"]=value_inp["*"]*jacob
    if " " in value_inp: # dsig(lab) -> dsig(cm)
      value_out[" "]=value_inp[" "]*jacob

  elif frame_inp["*"]=="C" and frame_out["*"]=="L": # sig(cm) -> sig(lab)
    if frame_inp["G"]=="L":
      ang3=value_inp["G"]
      cos3=math.cos(math.radians(ang3))
      (skip,p3,p3cmsq)=anglab_to_plab(id,ansan,m1,m2,m3,m4,ang3,cosh,sinh,invmassq)
      if skip:
        value_out["G"]="NaN"
        value_out["H"]="NaN"
        value_out["*"]="NaN"
        value_out[" "]="NaN"
        return skip,value_out
      ang3cm=anglab_to_angcm(m3,ang3,p3,cosh,sinh)
      sin3cm=math.sin(math.radians(ang3cm))
      cos3cm=math.cos(math.radians(ang3cm))
      p3cm=tinc_to_pcm(id,ansan,tinc,m1,m2,m3,m4)

    else:
      ang3cm=value_inp["G"]
      sin3cm=math.sin(math.radians(ang3cm))
      cos3cm=math.cos(math.radians(ang3cm))
      p3cm=tinc_to_pcm(id,ansan,tinc,m1,m2,m3,m4)
      e3cm=math.sqrt(m3**2+p3cm**2)
      p3=math.sqrt((p3cm*sin3cm)**2+(p3cm*cos3cm*cosh+e3cm*sinh)**2)

    e3cm=math.sqrt(m3**2+p3cm**2)
    jacob=abs(p3cm**2/p3**3*(p3cm*cosh+e3cm*cos3cm*sinh))
    value_out["*"]=value_inp["*"]/jacob
    if " " in value_inp: # dsig(cm) -> dsig(lab)
      value_out[" "]=value_inp[" "]/jacob

  else:
    value_out["*"]=value_inp["*"]
    if " " in value_inp:
      value_out[" "]=value_inp[" "]

  value_out["A"]=value_inp["A"]
  if "B" in value_inp:
    value_out["B"]=value_inp["B"]
  if "E" in value_inp:
    value_out["E"]=value_inp["E"]
  if "F" in value_inp:
    value_out["B"]=value_inp["F"]

  return skip,value_out


def transform_ddx(id,ansan,sf1,sf2,sf4,value_inp,frame_inp,frame_out):
  skip=False
  value_out=dict()

  tinc=value_inp["A"]
  m1=get_atomicweight(sf1)*ueV
  m2=get_atomicweight(sf2)*ueV
  m3=get_atomicweight(sf4)*ueV

  (cosh,sinh,invmassq)=get_lorentzfactor(m1,m2,tinc)

# transformation of energy (E) and its uncertainty (F)
  if frame_inp["E"]=="L":   # E in lab
    t3=value_inp["E"]
    e3=t3+m3
    p3=math.sqrt(e3**2-m3**2)
    if "F" in value_inp:
      de3=value_inp["F"]
      dp3=de3*(e3/p3)
    else:
      de3=0
      dp3=0
    if frame_inp["G"]=="L":   # theta in lab
      ang3=value_inp["G"]
      sin3=math.sin(math.radians(ang3))
      cos3=math.cos(math.radians(ang3))
      p3cm=math.sqrt((p3*sin3)**2+(p3*cos3*cosh-e3*sinh)**2) #p(lab) -> p(cm)
      e3cm=math.sqrt(m3**2+p3cm**2)

      if "H" in value_inp:
        dang3=value_inp["H"]
      else:
        dang3=0
      jacob1=abs(p3*sin3*sinh)                                # partial E(cm)/partial theta(lab)
#     jacob2=abs(-cos3*sinh)                                  # partial E(cm)/partial p(lab)
      jacob2=abs((p3/e3)*cosh-cos3*sinh)                      # partial E(cm)/partial p(lab)
      de3cm=math.sqrt((dang3*jacob1)**2+(dp3*jacob2)**2) # dtheta(lab),dp(lab) -> dE(cm)
      jacob1=abs((p3/p3cm**2)*(p3*cosh-e3*cos3*sinh))         # partial theta(cm)/partial theta(lab)
      jacob2=abs(-(m3**2*sin3*sinh)/(e3*p3cm**2))             # partial theta(cm)/partial p(lab)
      dang3cm=math.sqrt((dang3*jacob1)**2+(dp3*jacob2)**2) # dtheta(lab), dp(lab) -> dtheta(cm)

    else:                     # theta in c.m.
      ang3cm=value_inp["G"]
      sin3cm=math.sin(math.radians(ang3cm))
      cos3cm=math.cos(math.radians(ang3cm))
      (skip,p3cm)=plabangcm_to_pcm(id,ansan,m3,p3,ang3cm,cosh,sinh)
      if skip:
        value_out["E"]="NaN"
        value_out["F"]="NaN"
        value_out["G"]="NaN"
        value_out["H"]="NaN"
        value_out["*"]="NaN"
        value_out[" "]="NaN"
        return skip,value_out
      e3cm=math.sqrt(m3**2+p3cm**2)
      if "H" in value_inp:
        dang3cm=value_inp["H"]
      else:
        dang3cm=0
      (jacob1,jacob2)=get_jacobian_angcmplab_to_pcm(m3,ang3cm,p3,cosh,sinh)
      dp3cm=math.sqrt((dang3cm*jacob1)**2+(dp3*jacob2)**2) # dtheta(cm), dp(lab) -> dp(cm)
      de3cm=dp3cm*(p3cm/e3cm)
      jacob1=abs((p3cm/p3**2)*(p3cm*cosh+e3cm*cos3cm*sinh))  # partial theta(lab)/partial theta(cm)
      jacob2=abs((m3**2*sin3cm*sinh)/(e3cm*p3**2))           # partial theta(lab) / partial p(cm)
      dang3=math.sqrt((dang3cm*jacob1)**2+(dp3cm*jacob2)**2) # dtheta(cm), dp(cm) -> dtheta(lab)

    t3cm=e3cm-m3

  else:                     # E in cm
    t3cm=value_inp["E"]
    e3cm=t3cm+m3
    p3cm=math.sqrt(e3cm**2-m3**2)
    if "F" in value_inp:
      de3cm=value_inp["F"]
      dp3cm=de3cm*(e3cm/p3cm)
    else:
      de3cm=0
      dp3cm=0
    if frame_inp["G"]=="C":   # theta in c.m.
      ang3cm=value_inp["G"]
      sin3cm=math.sin(math.radians(ang3cm))
      cos3cm=math.cos(math.radians(ang3cm))
      p3=math.sqrt((p3cm*sin3cm)**2+(p3cm*cos3cm*cosh+e3cm*sinh)**2)
      e3=math.sqrt(m3**2+p3**2)

      if "H" in value_inp:
        dang3cm=value_inp["H"]
      else:
        dang3cm=0
      jacob1=abs(-p3cm*sin3cm*sinh)            # partial E(lab)/partial theta(cm)
#     jacob2= cos3cm*sinh                      # partial E(lab)/partial p(cm)
      jacob2=abs((p3cm/e3cm)*cosh+cos3cm*sinh) # partial E(lab)/partial p(cm)
      de3=math.sqrt((dang3cm*jacob1)**2+(dp3cm*jacob2)**2) # dtheta(cm),dp(cm) -> dE(lab)
      jacob1=abs((p3cm/p3**2)*(p3cm*cosh+e3cm*cos3cm*sinh)) # partial theta(lab)/partial theta(cm)
      jacob2=abs((m3**2*sin3cm*sinh)/(e3cm*p3**2))          # partial theta(lab)/partial p(cm)
      dang3=math.sqrt((dang3cm*jacob1)**2+(dp3cm*jacob2)**2) # dtheta(cm), dp(cm) -> dtheta(lab)

    else:                     # theta in lab
      ang3=value_inp["G"]
      sin3=math.sin(math.radians(ang3))
      cos3=math.cos(math.radians(ang3))
      (skip,p3)=pcmanglab_to_plab(id,ansan,m3,p3cm,ang3,cosh,sinh)
      if skip:
        value_out["E"]="NaN"
        value_out["F"]="NaN"
        value_out["G"]="NaN"
        value_out["H"]="NaN"
        value_out["*"]="NaN"
        value_out[" "]="NaN"
        return skip,value_out
      e3=math.sqrt(m3**2+p3**2)
      if "H" in value_inp:
        dang3=value_inp["H"]
      else:
        dang3=0
      (jacob1,jacob2)=get_jacobian_anglabpcm_to_plab(m3,ang3,p3cm,cosh,sinh)
      dp3=math.sqrt((dang3*jacob1)**2+(dp3cm*jacob2)**2) # dheta(lab), dp(cm) -> dp(lab)
      de3=dp3*(p3/e3)
      jacob1=abs((p3/p3cm**2)*(p3*cosh-e3*cos3*sinh))           # partial theta(cm)/partial theta(lab)
      jacob2=abs(-(m3**2*sin3*sinh)/(e3*p3cm**2))               # partial theta(cm)/partial p(lab)
      dang3cm=math.sqrt((dang3*jacob1)**2+(dp3*jacob2)**2) # dtheta(lab), dp(lab) -> dtheta(cm)

    t3=e3-m3

  if frame_out["E"]=="L":
    value_out["E"]=t3
    if de3!=0:
      value_out["F"]=de3
  else:
    value_out["E"]=t3cm
    if de3cm!=0:
      value_out["F"]=de3cm

# transformation of angle (G) and its uncertainty (H)
  if frame_inp["G"]=="L":
    ang3=value_inp["G"]
    sin3=math.sin(math.radians(ang3))
    cos3=math.cos(math.radians(ang3))
        
    if frame_out["G"]=="C": # theta(lab) -> theta(cm)
      tan3cm=p3*sin3/(p3*cos3*cosh-e3*sinh)
      ang3cm=math.degrees(math.atan(tan3cm))
      if ang3cm<0:
        ang3cm=ang3cm+180

  elif frame_inp["G"]=="C" and frame_out["G"]=="L": # theta(cm) -> theta(lab)
    ang3cm=value_inp["G"]
    sin3cm=math.sin(math.radians(ang3cm))
    cos3cm=math.cos(math.radians(ang3cm))

    if frame_out["G"]=="L": # theta(cm) -> theta(lab)
      tan3=p3cm*sin3cm/(p3cm*cos3cm*cosh+e3cm*sinh)
      ang3=math.degrees(math.atan(tan3))
      if ang3<0:
        ang3=ang3+180

  if frame_out["G"]=="L":
    value_out["G"]=ang3
    if dang3!=0:
      value_out["H"]=dang3
  else:
    value_out["G"]=ang3cm
    if dang3cm!=0:
      value_out["H"]=dang3cm


# transformation of cross section (*) and its uncertainty ( )
  jacob=p3cm/p3
  if frame_inp["*"]=="L" and frame_out["*"]=="C": # sigma(lab) -> sigma(cm)
    value_out["*"]=value_inp["*"]*jacob
    if " " in value_inp:
      value_out[" "]=value_inp[" "]*jacob
  elif frame_inp["*"]=="C" and frame_out["*"]=="L": # sigma(lab) -> sigma(cm)
    value_out["*"]=value_inp["*"]/jacob
    if " " in value_inp:
      value_out[" "]=value_inp[" "]/jacob
  else:
    value_out["*"]=value_inp["*"]
    if " " in value_inp:
      value_out[" "]=value_inp[" "]

  value_out["A"]=value_inp["A"]
  if "B" in value_inp:
    value_out["B"]=value_inp["B"]

  return skip,value_out


def get_lorentzfactor(m1,m2,t2):
  e2=t2+m2
  p2sq=e2**2-m2**2
  p2=math.sqrt(p2sq)
  invmassq=(m1+e2)**2-p2sq
  cosh=(m1+e2)/math.sqrt(invmassq)
  sinh=p2/math.sqrt(invmassq)

  return cosh,sinh,invmassq


def get_jacobian_angcmplab_to_pcm(m3,ang3cm,p3,cosh,sinh):
  sin3cm=math.sin(math.radians(ang3cm))
  cos3cm=math.cos(math.radians(ang3cm))
  e3=math.sqrt(m3**2+p3**2)

# partial p(cm)/partial theta(cm)
  jacob1=e3*sin3cm*sinh*(2+cos3cm**2*sinh**2) \
         /(1+sin3cm**2*sinh**2)**2 \
        -sin3cm*cos3cm*sinh**2*cosh*(m3**2-m3**2*sin3cm**2*sinh**2+2*p3**2) \
         /((1+sin3cm**2*sinh**2)**2*math.sqrt(p3**2-m3**2*sin3cm**2*sinh**2))

# partial p(cm)/partial p(lab)
  jacob2=p3/(1+sin3cm**2*sinh**2) \
         *(-cos3cm*sinh/e3+cosh/math.sqrt(p3**2-m3**2*sin3cm**2*sinh**2))

  jacob1=abs(jacob1)
  jacob2=abs(jacob2)

  return jacob1, jacob2


def get_jacobian_anglabpcm_to_plab(m3,ang3,p3cm,cosh,sinh):
  sin3=math.sin(math.radians(ang3))
  cos3=math.cos(math.radians(ang3))
  e3cm=math.sqrt(m3**2+p3cm**2)

# partial p(lab)/partial theta(lab)
  jacob1=-e3cm*sin3*sinh*(2+cos3**2*sinh**2) \
         /(1+sin3**2*sinh**2)**2 \
         -sin3*cos3*sinh**2*cosh*(m3**2-m3**2*sin3**2*sinh**2+2*p3cm**2) \
         /((1+sin3**2*sinh**2)**2*math.sqrt(p3cm**2-m3**2*sin3**2*sinh**2))

# partial p(lab)/partial p(cm)
  jacob2=p3cm/(1+sin3**2*sinh**2) \
         *(cos3*sinh/e3cm+cosh/math.sqrt(p3cm**2-m3**2*sin3**2*sinh**2))

  jacob1=abs(jacob1)
  jacob2=abs(jacob2)

  return jacob1, jacob2


def plabangcm_to_pcm(id,ansan,m3,p3,ang3cm,cosh,sinh):
  skip=False

  e3=math.sqrt(m3**2+p3**2)
  sin3cm=math.sin(math.radians(ang3cm))
  cos3cm=math.cos(math.radians(ang3cm))
  d=p3**2-m3**2*sin3cm**2*sinh**2
  if d<0:
    msg=ansan+" point # "+'{:>5}'.format(str(id+1))+": Discriminant negative"
    print_error(msg,"",True)
    skip=True
    p3cm="NaN"
    return skip,p3cm

  p3cma=(-e3*cos3cm*sinh+cosh*math.sqrt(d))/(1+sin3cm**2*sinh**2)
  p3cmb=(-e3*cos3cm*sinh-cosh*math.sqrt(d))/(1+sin3cm**2*sinh**2)
  if p3cma>0 and p3cmb>0:
    msg=ansan+" point # "+'{:>5}'.format(str(id+1))+": Two plab values exist for a given anglab"
    print_error(msg,"",True)
    skip=True
    p3cm="NaN"
  elif p3cma<0 and p3cmb<0:
    msg=ansan+" point # "+'{:>5}'.format(str(id+1))+": No positive plab value exists for a given angcm"
    print_error(msg,"",True)
    skip=True
    p3cm="NaN"
  else:
    p3cm=p3cma

  return skip,p3cm


def pcmanglab_to_plab(id,ansan,m3,p3cm,ang3,cosh,sinh):
  skip=False

  e3cm=math.sqrt(m3**2+p3cm**2)
  sin3=math.sin(math.radians(ang3))
  cos3=math.cos(math.radians(ang3))
  d=p3cm**2-m3**2*sin3**2*sinh**2

  if d<0:
    msg=ansan+" point # "+'{:>5}'.format(str(id+1))+": Discriminant negative"
    print_error(msg,"",True)
    skip=True
    p3="NaN"
    return skip,p3

  p3a=(e3cm*cos3*sinh+cosh*math.sqrt(d))/(1+sin3**2*sinh**2)
  p3b=(e3cm*cos3*sinh-cosh*math.sqrt(d))/(1+sin3**2*sinh**2)
  if p3a>0 and p3b>0:
    msg=ansan+" point # "+'{:>5}'.format(str(id+1))+": Two plab values exist for a given anglab"
    print_error(msg,"",True)
    skip=True
    p3="NaN"
  elif p3a<0 and p3b<0:
    msg=ansan+" point # "+'{:>5}'.format(str(id+1))+": No positive plab value exists for a given anglab"
    print_error(msg,"",True)
    skip=True
    p3="NaN"
  else:
    p3=p3a

  return skip,p3


def anglab_to_plab(id,ansan,m1,m2,m3,m4,ang3,cosh,sinh,invmassq):
  skip=False

  p3cmsq=((invmassq-m3**2-m4**2)**2-4*m3**2*m4**2)/(4*invmassq)
  e3cm=math.sqrt(m3**2+p3cmsq)

  sin3=math.sin(math.radians(ang3))
  cos3=math.cos(math.radians(ang3))
     
  d=p3cmsq-m3**2*sin3**2*sinh**2

  if d<0:
    msg=ansan+" point # "+'{:>5}'.format(str(id+1))+": Discriminant negative"
    print_error(msg,"",True)
    skip=True
    p3="NaN"
  else:
    p3a=(e3cm*cos3*sinh+cosh*math.sqrt(d))/(1+sin3**2*sinh**2)
    p3b=(e3cm*cos3*sinh-cosh*math.sqrt(d))/(1+sin3**2*sinh**2)
    if p3a>0 and p3b>0:
      msg=ansan+" point # "+'{:>5}'.format(str(id+1))+": Two plab values exist for a given anglab"
      print_error(msg,"",True)
      skip=True
      p3="NaN"
    elif p3a<0 and p3b<0:
      msg=ansan+" point # "+'{:>5}'.format(str(id+1))+": No positive plab value exists for a given anglab"
      print_error(msg,"",True)
      skip=True
      p3="NaN"
    else:
      p3=p3a

  return skip,p3,p3cmsq


def anglab_to_angcm(m3,ang3,p3,cosh,sinh):
  cos3=math.cos(math.radians(ang3))
  sin3=math.sin(math.radians(ang3))

  e3=math.sqrt(p3**2+m3**2)

  tan3cm=p3*sin3/(p3*cos3*cosh-e3*sinh)
  ang3cm=math.degrees(math.atan(tan3cm))
  if ang3cm<0:
    ang3cm=ang3cm+180

  return ang3cm


def angcm_to_anglab(m3,ang3cm,p3cm,cosh,sinh):
  sin3cm=math.sin(math.radians(ang3cm))
  cos3cm=math.cos(math.radians(ang3cm))
  e3cm=math.sqrt(m3**2+p3cm**2)
  tan3=p3cm*sin3cm/(p3cm*cos3cm*cosh+e3cm*sinh)
  ang3=math.degrees(math.atan(tan3))
  if ang3<0:
    ang3=ang3+180

  return ang3


def tinc_to_pcm(id,ansan,tinc,m1,m2,m3,m4):
  invmassq=(m1+tinc+m2)**2-((tinc+m2)**2-m2**2)
  if ((invmassq-m3**2-m4**2)**2-4*m3**2*m4**2)/(4*invmassq)<0:
    msg=ansan+" point # "+'{:>5}'.format(str(id+1))+": Invariant mass squared negative"
    print_error_fatal(msg,"")
  pcm=math.sqrt(((invmassq-m3**2-m4**2)**2-4*m3**2*m4**2)/(4*invmassq))

  return pcm


def get_atomicweight(code):
  partnucl= {'A'   : '2-HE-4'
            ,'AN'  : '0-AN-1'
            ,'AP'  : '1-AP-1'
            ,'D'   : '1-H-2'
            ,'ETA' : '0-ET-0'
            ,'G'   : '0-G-0'
            ,'HE3' : '2-HE-3'
            ,'KN'  : '1-KN-0'
            ,'KP'  : '1-KP-0'
            ,'K0'  : '0-K0-0'
            ,'N'   : '0-NN-1'
            ,'P'   : '1-H-1'
            ,'PI0' : '0-P0-0'
            ,'PIN' : '1-PN-0'
            ,'PIP' : '1-PP-0'
            ,'T'   : '1-H-3'}

  aw=0
  if not re.compile(r"^(\d+)\-([A-Z][A-Z0]?|\*)\-(\d+)(-(G|M\d?|L\d))?$").search(code):
    if code in partnucl:
      code=partnucl[code]
    else:
      aw=-1

  if aw!=-1:
    aw=dict_retrieval("227","code",code,"atomic_weight")
    if aw is None:
      aw=-1

  return aw


def dict_retrieval(dict_id,field_inp,value_inp,field_out):
  l=[x[field_out] for x in dict_json[dict_id] if x[field_inp]==value_inp]

  if len(l)==0 and dict_id=="227": # retrieve nuclide code with -G
    value_inp_org=value_inp
    if not re.compile(r"-G$").search(value_inp):
      value_inp=value_inp+"-G"
      l=[x[field_out] for x in dict_json[dict_id] if x[field_inp]==value_inp]

  if len(l)==0:
    msg="code "+value_inp_org+" cannot be resolved by Dictionary "+dict_id
    line=""
    print_error_fatal(msg,"")
    value_out=None
  else:
    value_out=l[0]

  return value_out


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
   usage="Transform variables between lab. and c.m. system",\
   epilog="example: ./x4_lotran.py -P E1705.007 -q adx -1 82-PB-208 -2 D -3 P -4 82-PB-209 -t 22E+06 -a 35.21 -c 1.666E-03 -C 0.030E-03 -x 2.032E+06 -s CC -S LL")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-d", "--file_dict",\
   help="input JSON dictionary (optional, default: dict.json)", default="dict.json")
  parser.add_argument("-g", "--file_log",\
   help="output log file (optional, default: x4_lotran.log)", default="x4_lotran.log")
  parser.add_argument("-p", "--id",\
   help="data point # (optional, default: 1)", default="1")
  parser.add_argument("-P", "--ansan",\
   help="dataset # (e.g., EXFOR dataset #)")
  parser.add_argument("-q", "--quan",\
   help="physical quantity (ADX or DDX)")
  parser.add_argument("-1", "--sf1",\
   help="target (EXFOR SF1)")
  parser.add_argument("-2", "--sf2",\
   help="projectile (EXFOR SF2)")
  parser.add_argument("-3", "--sf3",\
   help="ejectile (EXFOR SF3)")
  parser.add_argument("-4", "--sf4",\
   help="residual (EXFOR SF4)")
  parser.add_argument("-t", "--tinc",\
   help="laboratory incident kinetic energy, eV")
  parser.add_argument("-a", "--ang3",\
   help="ejectile angle, deg)")
  parser.add_argument("-A", "--dang3",\
   help="ejectile angle uncertainty, deg (optional, default: 0)", default="0")
  parser.add_argument("-e", "--e3",\
   help="ejectile kinetic energy (eV)")
  parser.add_argument("-E", "--de3",\
   help="ejectile kinetic energy uncertainty, eV (optional, default: 0)", default="0")
  parser.add_argument("-c", "--sig",\
   help="cross section,  b/sr or b/sr/eV")
  parser.add_argument("-C", "--dsig",\
   help="cross section uncertainty, b/sr or b/sr/eV (optional, default: 0)", default="0")
  parser.add_argument("-x", "--eexc",\
   help="residual excitation energy (eV)")
  parser.add_argument("-s", "--sysinp",\
   help="input reference system")
  parser.add_argument("-S", "--sysout",\
   help="output reference system")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("LOTRAN (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force
  value_inp=dict()
  frame_inp=dict()
  frame_out=dict()

  file_dict=args.file_dict
  print("JSON Dictionary ----------------------------------> "+file_dict)
  if not os.path.exists(file_dict):
    print(" ** File "+file_dict+" does not exist.")
  while not os.path.exists(file_dict):
    file_dict=input("JSON DIctionary [dict.json] ----------------------> ")
    if file_dict=="":
      file_dict="dict.json"
    if not os.path.exists(file_dict):
      print(" ** File "+file_dict+" does not exist.")

  file_log=args.file_log
  print("output log file ----------------------------------> "+file_log)
  if os.path.isfile(file_log):
    msg="File '"+file_log+"' exists and must be overwritten."
    print_error(msg,"",force0)

  id=args.id
  print("data point # -------------------------------------> "+id)
  id=int(id)-1

  ansan=args.ansan
  if ansan is None:
    ansan=input("Dataset # (e.g., EXFOR Dataset #) [22742.002] ----> ")
  if ansan=="":
    ansan="22742.002"

  quan=args.quan
  if quan is not None:
    quan=quan.upper()
  if quan is None:
    quan=input("quantity type - ADX or DDX [ADX] -----------------> ")
  quan=quan.upper()
  if quan=="":
    quan="ADX"
  if quan!="ADX" and quan!="DDX":
    print(" ** "+quan+" is invalid. Must be ADX or DDX.")
    while quan!="ADX" and quan!="DDX":
      print(" ** "+quan+" must be ADX or DDX.")
      quan=input("quantity type - ADX or DDX [ADX] -----------------> ")
      if quan=="":
        quan="ADX"

  sf1=args.sf1
  sf1=check_nuclide_symbol(sf1,"target (EXFOR SF1) ----")

  sf2=args.sf2
  sf2=check_nuclide_symbol(sf2,"projectile (EXFOR SF2) ")

  sf3=args.sf3
  sf3=check_nuclide_symbol(sf3,"ejectile (EXFOR SF3) --")

  sf4=args.sf4
  sf4=check_nuclide_symbol(sf4,"residual (EXFOR SF4) --")

  tinc=args.tinc
  tinc=receive_positive_float(tinc,"laboratory incident kinetic energy (eV) ---------", False)
  value_inp["A"]=tinc

  ang3=args.ang3
  ang3=receive_positive_float(ang3,"ejectile angle (deg) ----------------------------", True)
  value_inp["G"]=ang3

  dang3=args.dang3
  print("ejectile angle uncertainty (deg) -----------------> "+dang3)
  dang3=receive_positive_float(dang3,"ejectile angle uncertainty (deg) ----------------", True)
  if dang3!=0:
    value_inp["H"]=dang3

  if quan=="DDX":
    e3=args.e3
    e3=receive_positive_float(e3,"ejectile kinetic energy (eV) --------------------", False)
    value_inp["E"]=e3

    de3=args.de3
    print("ejectile kinetic energy uncertainty (eV) ---------> "+de3)
    de3=receive_positive_float(de3,"ejectile kinetic energy uncertainty (eV) --------", True)
    if de3!=0:
      value_inp["F"]=de3

  if quan=="ADX":
    sig=args.sig
    sig=receive_positive_float(sig,"angular diff. cross section (b/sr) --------------", False)
    value_inp["*"]=sig
    dsig=args.dsig
    print("angular diff. cross section uncertainty (b/sr) ---> "+dsig)
    dsig=receive_positive_float(dsig,"angular diff. cross section uncertainty (b/sr) --", True)
    if dsig!=0:
      value_inp[" "]=dsig

  else:
    sig=args.sig
    sig=receive_positive_float(sig,"double diff. cross section (b/sr/eV) ------------", False)
    value_inp["*"]=sig
    dsig=args.dsig
    print("double diff. cross section uncertainty (b/sr/eV) ---> "+dsig)
    dsig=receive_positive_float(dsig,"double diff. cross section uncertainty (b/sr/eV) ", True)
    if dsig!=0:
      value_inp[" "]=dsig

  eexc=args.eexc
  if quan=="ADX":
    eexc=receive_positive_float(eexc,"residual excitation energy ----------------------", True)
    value_inp["E"]=eexc
       
  sysinp=args.sysinp
  if quan=="ADX":
    if sysinp is None:
      sysinp=input("input reference system identifier [LL] -----------> ")
    if sysinp=="":
      sysinp="LL"
    else:
      sysinp=sysinp.upper()
    if not re.compile(r"^(L|C)(L|C)$").search(sysinp):
      print(" ** "+sysinp+" is an invalid reference system identifier. Must be a 2-character combination of L and C.")
    while not re.compile(r"^(L|C)(L|C)$").search(sysinp):
      sysinp=input("input reference system identifier [LL] -----------> ")
      if sysinp=="":
        sysinp="LL"
      sysinp=sysinp.upper()
      if not re.compile(r"^(L|C)(L|C)$").search(sysinp):
        print(" ** "+sysinp+" is an invalid reference system identifier. Must be a 2-character combination of o, l and c.")
  elif quan=="DDX":
    if sysinp is None:
      sysinp=input("input reference system identifier [LLL] ----------> ")
    if sysinp=="":
      sysinp="LLL"
    else:
      sysinp=sysinp.upper()
    if not re.compile(r"^(L|C)(L|C)(L|C)$").search(sysinp):
      print(" ** "+sysinp+" is an invalid reference system identifier. Must be a 3-character combination of L and C.")
    while not re.compile(r"^(L|C)(L|C)(L|C)$").search(sysinp):
      sysinp=input("input reference system identifier [LLL] -----------> ")
      if sysinp=="":
        sysinp="LLL"
      sysinp=sysinp.upper()
      if not re.compile(r"^(L|C)(L|C)(L|C)$").search(sysinp):
        print(" ** "+sysinp+" is an invalid reference system identifier. Must be a 3-character combination of o, l and c.")
  frame_inp["*"]=sysinp[0:1]
  frame_inp["G"]=sysinp[1:2]
  if quan=="DDX":
    frame_inp["E"]=sysinp[2:3]

  sysout=args.sysout
  if quan=="ADX":
    if sysout is None:
      sysout=input("output reference system identifier [OO] ----------> ")
    if sysout=="":
      sysout="OO"
    else:
      sysout=sysout.upper()
    if not re.compile(r"^(O|L|C)(O|L|C)$").search(sysout):
      print(" ** "+sysout+" is an invalid reference system identifier. Must be a 2-character combination of L and C.")
    while not re.compile(r"^(O|L|C)(O|L|C)$").search(sysout):
      sysout=input("output reference system identifier [OO] ----------> ")
      if sysout=="":
        sysout="OO"
      sysout=sysout.upper()
      if not re.compile(r"^(O|L|C)(O|L|C)$").search(sysout):
        print(" ** "+sysout+" is an invalid reference system identifier. Must be a 2-character combination of o, l and c.")
  elif quan=="DDX":
    if sysout is None:
      sysout=input("output reference system identifier [OOO] ---------> ")
    if sysout=="":
      sysout="OOO"
    else:
      sysout=sysout.upper()
    if not re.compile(r"^(O|L|C)(O|L|C)(O|L|C)$").search(sysout):
      print(" ** "+sysout+" is an invalid reference system identifier. Must be a 3-character combination of L and C.")
    while not re.compile(r"^(O|L|C)(O|L|C)(O|L|C)$").search(sysout):
      sysout=input("output reference system identifier [OOO] ---------> ")
      if sysout=="":
        sysout="OOO"
      sysout=sysout.upper()
      if not re.compile(r"^(O|L|C)(O|L|C)(O|L|C)$").search(sysout):
        print(" ** "+sysout+" is an invalid reference system identifier. Must be a 3-character combination of o, l and c.")
  frame_out["*"]=sysout[0:1]
  if frame_out["*"]=="O":
     frame_out["*"]=frame_inp["*"]
  frame_out["G"]=sysout[1:2]
  if frame_out["G"]=="O":
     frame_out["G"]=frame_inp["G"]
  if quan=="DDX":
    frame_out["E"]=sysout[2:3]
    if frame_out["E"]=="O":
       frame_out["E"]=frame_inp["E"]

  return file_dict,file_log,id,ansan,quan,sf1,sf2,sf3,sf4,value_inp,frame_inp,frame_out,force0


def check_nuclide_symbol(code,name):
  partnucl= {'A'   : '2-HE-4'
            ,'AN'  : '0-AN-1'
            ,'AP'  : '1-AP-1'
            ,'D'   : '1-H-2'
            ,'ETA' : '0-ET-0'
            ,'G'   : '0-G-0'
            ,'HE3' : '2-HE-3'
            ,'KN'  : '1-KN-0'
            ,'KP'  : '1-KP-0'
            ,'K0'  : '0-K0-0'
            ,'N'   : '0-NN-1'
            ,'P'   : '1-H-1'
            ,'PI0' : '0-P0-0'
            ,'PIN' : '1-PN-0'
            ,'PIP' : '1-PP-0'
            ,'T'   : '1-H-3'}

  if code is None:
    code=""
  else:
    code=code.upper()
  if re.compile(r"^(\d+)\-([A-Z][A-Z0]?|\*)\-(\d+)(-(G|M\d?|L\d))?$").search(code):
    return code
  if code in partnucl:
    code=partnucl[code]
    return code
  elif code=="X" and "SF3" in name:
    return code
  code=input(name+"---------------------------> ")
  code=code.upper()
  if re.compile(r"^(\d+)\-([A-Z][A-Z0]?|\*)\-(\d+)(-(G|M\d?|L\d))?$").search(code):
    return code
  if code in partnucl:
    code=partnucl[code]
    return code
  elif code=="X" and "SF3" in name:
    return code
  while not re.compile(r"^(\d+)\-([A-Z][A-Z0]?|\*)\-(\d+)(-(G|M\d?|L\d))?$").search(code):
    print(" ** "+code+" is not a valid EXFOR code.")
    code=input(name+"---------------------------> ")
    code=code.upper()
    if code in partnucl:
      code=partnucl[code]
      return code
    elif code=="X" and "SF3" in name:
      return code
  return code


def receive_positive_float(value,name,allowzero):
  if value is None:
    value=input(name+"-> ")
  if value=="":
    value=0
  try:
    value=float(value)
  except (ValueError,TypeError):
    value=""
  while value=="" or value<0 or (value==0 and not allowzero):
    print(" ** "+str(value)+" is invalid. Must be positive float or integer.")
    value=input(name+"-> ")
    try:
      value=float(value)
    except (ValueError,TypeError):
      value=""

  return value


def print_error(msg,line,force):
  print("** "+msg)
  if line!="":
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


def print_error_fatal(msg,line):
  print("**  "+msg)
  print(line)
  exit()


if __name__ == "__main__":
  lotran()
  exit()
