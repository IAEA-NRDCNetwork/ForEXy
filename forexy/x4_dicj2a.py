#!/usr/bin/python3
ver="2026.06.24"
############################################################
# DICJ2A Ver.2026.06.24
# (Converter from JSON Dictionary to Archive Dictionary)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
#  on behalf of the International Network of
#  Nuclear Reaction Data Centres (NRDC)
############################################################
import time
import datetime
import json
import os
import re
import argparse

def dicj2a():
  args=get_args(ver)
  main(*get_input(args))


def main(dict_ver,dir_json,dir_archive,force0):
  time_start=time.time()

  global dict_full

  force=force0

  dict_full=dict()

  dictionary_list=[
  "001",  "002", "003", "004", "005", "006", "007", "008",
  "015",  "016", "017", "018", "019",
  "020",  "021", "022", "023", "024", "025", "026",
  "030",  "031", "032", "033", "034", "035", "037", "038",
  "043",  "045", "047", "048", "049", 
  "052", 
  "113",  "144",
  "207",  "209", "213", "227", "235", "236"]

  dictionary_list_add=["950"]
  dictionary_list=dictionary_list+dictionary_list_add


# Read JSON Dictionary
  file_in=dir_json+"/dict_"+dict_ver+".json"
  if os.path.exists(file_in):
    f=open(file_in, 'r')
    dict_full=json.load(f)
    f.close()
  else:
    msg="File "+file_in+" does not exist."
    line=""
    print_error_fatal(msg,line)


# Produce Archive Dictionary
  print("printing archive dictionary   ... ", end="")
  for dict_id in dictionary_list:
    print(dict_id, end=" ")
    json_to_archive(dict_ver,dir_archive,dict_id)
  print()

  time_end=time.time()
  time_elapsed=format(time_end-time_start, ".2f")
  print("DICJ2A: Processing terminated normally. "+time_elapsed+" sec.\n")


def json_to_archive(dict_ver,dir_archive,dict_id):
  file_out=dir_archive+"/archive."+dict_id+"."+dict_ver

  if dict_id=="950":
    file_out=dir_archive+"/dict_arc.top"
  else:
    file_out=dir_archive+"/dict_arc_new."+dict_id
  f=open(file_out,'w')

  for j,record in enumerate(dict_full[dict_id]):

    for item in record:
      if record[item] is None:
        dict_full[dict_id][j][item]=""

    code=get_code(dict_id,record)
    if code=="":
      for i,comment in enumerate(dict_full[dict_id][j]["comment"]):
        char=" "\
            +"%-3s"  % dict_full[dict_id][j]["status_code"]\
            +" "*39
        if dict_id=="005" or dict_id=="006" or\
           dict_id=="007" or dict_id=="015":
          char+=dict_full[dict_id][j]["comment"][i]["comment_flag"]
          char+=dict_full[dict_id][j]["comment"][i]["comment"]
        elif dict_id=="016":
          char+=dict_full[dict_id][j]["comment"][i]["comment"]
          char+=" "*(103-len(char))
          char+=dict_full[dict_id][j]["comment"][i]["comment_flag"]
        elif dict_id=="020" or dict_id=="037" or\
             dict_id=="236":
          char+=dict_full[dict_id][j]["comment"][i]
        elif dict_id=="033":
          char+="  "+dict_full[dict_id][j]["comment"][i]

        char+=" "*(123-len(char))
        f.write(char+"\n")

    else:

      if dict_id!="950":
        char="%-1s"  % dict_full[dict_id][j]["alteration_flag"]\
            +"%-3s"  % dict_full[dict_id][j]["status_code"]\
            +" "\
            +"%-6s"  % dict_full[dict_id][j]["date"]\
            +" "

      if dict_id=="001":
        char+=json_to_archive_001(code,j)
     
      elif dict_id=="002":
        char+=json_to_archive_002(code,j)
     
      elif dict_id=="003":
        char+=json_to_archive_003(code,j)
     
      elif dict_id=="004":
        char+=json_to_archive_004(code,j)
     
      elif dict_id=="005":
        char+=json_to_archive_005(code,j)
     
      elif dict_id=="006":
        char+=json_to_archive_006(code,j)
     
      elif dict_id=="007" or dict_id=="207":
        char+=json_to_archive_gen_1(code,j,dict_id)
     
      elif dict_id=="008":
        char+=json_to_archive_008(code,j)
     
      elif dict_id=="015":
        char+=json_to_archive_015(code,j)
     
      elif dict_id=="016":
        char+=json_to_archive_016(code,j)
     
      elif dict_id=="017":
        char+=json_to_archive_017(code,j)
     
      elif dict_id=="018" or dict_id=="021" or\
           dict_id=="022" or dict_id=="023":
        char+=json_to_archive_gen_2(code,j,dict_id)
     
      elif dict_id=="019":
        char+=json_to_archive_019(code,j)
     
      elif dict_id=="020" or dict_id=="037" or\
           dict_id=="038":
        char+=json_to_archive_gen_3(code,j,dict_id)
     
      elif dict_id=="024":
        char+=json_to_archive_024(code,j)
     
      elif dict_id=="025":
        char+=json_to_archive_025(code,j)
     
      elif dict_id=="026":
        char+=json_to_archive_026(code,j)
     
      elif dict_id=="030":
        char+=json_to_archive_030(code,j)
     
      elif dict_id=="031":
        char+=json_to_archive_031(code,j)
     
      elif dict_id=="032":
        char+=json_to_archive_032(code,j)
     
      elif dict_id=="033":
        char+=json_to_archive_033(code,j)
     
      elif dict_id=="034":
        char+=json_to_archive_034(code,j)
     
      elif dict_id=="035":
        char+=json_to_archive_035(code,j)
     
      elif dict_id=="043":
        char+=json_to_archive_043(code,j)
     
      elif dict_id=="045":
        char+=json_to_archive_045(code,j)
     
      elif dict_id=="047":
        char+=json_to_archive_047(code,j)
     
      elif dict_id=="048":
        char+=json_to_archive_048(code,j)
     
      elif dict_id=="049":
        char+=json_to_archive_049(code,j)
     
      elif dict_id=="052":
        char+=json_to_archive_052(code,j)
     
      elif dict_id=="113":
        char+=json_to_archive_113(code,j)
     
      elif dict_id=="144":
        char+=json_to_archive_144(code,j)
     
      elif dict_id=="209":
        char+=json_to_archive_209(code,j)
     
      elif dict_id=="213":
        char+=json_to_archive_213(code,j)
     
      elif dict_id=="227":
        char+=json_to_archive_227(code,j)
     
      elif dict_id=="235":
        char+=json_to_archive_235(code,j)
     
      elif dict_id=="236":
        char+=json_to_archive_236(code,j)
     
      elif dict_id=="950":
        char=json_to_archive_top(code,j)

      f.write(char+"\n")

      if "long_expansion" in dict_full[dict_id][j]:
        long_expansion=dict_full[dict_id][j]["long_expansion"]
        if long_expansion!="":
          print_long_expansion_archive(f,long_expansion,j,dict_id)

      if "comment" in dict_full[dict_id][j]:
        for i, comment in enumerate(dict_full[dict_id][j]["comment"]):
          if dict_id=="003" or dict_id=="005" or\
             dict_id=="006" or dict_id=="007" or\
             dict_id=="016" or dict_id=="034" or\
             dict_id=="207":
            comment_flag=dict_full[dict_id][j]["comment"][i]["comment_flag"]
            comment=dict_full[dict_id][j]["comment"][i]["comment"]
            char="%-1s"  % dict_full[dict_id][j]["alteration_flag"]\
                +"%-3s"  % dict_full[dict_id][j]["status_code"]\
                +" "*8\
                +" "*31

            if dict_id=="016":
              char=char\
                  +comment
            else:
              char=char\
                  +comment_flag\
                  +comment
           
          elif dict_id=="033" or dict_id=="209":
            char="%-1s"  % dict_full[dict_id][j]["alteration_flag"]\
                +"%-3s"  % dict_full[dict_id][j]["status_code"]\
                +" "*8\
                +" "*31\
                +" "*2\
                +comment

          else:
            char="%-1s"  % dict_full[dict_id][j]["alteration_flag"]\
                +"%-3s"  % dict_full[dict_id][j]["status_code"]\
                +" "*8\
                +" "*31\
                +comment\
       
       
          char+=" "*(123-len(char))
          f.write(char+"\n")

  f.close()


def json_to_archive_001(code,j):
  char="%-10s" % code\
      +" "*21\
      +"%9s"   % dict_full["001"][j]["internal_numerical_equivalent"]\
      +" "\
      +"%-55s" % dict_full["001"][j]["expansion"]\
      +" "*15

  return char


def json_to_archive_002(code,j):
  char="%-10s" % code\
      +" "*21\
      +"%-25s" % dict_full["002"][j]["expansion"]\
      +"%-1s"  % dict_full["002"][j]["keyword_required"]\
      +"%2s"   % dict_full["002"][j]["internal_numerical_equivalent"]\
      +"%-1s"  % dict_full["002"][j]["code_required"]\
      +"%3s"   % dict_full["002"][j]["pointer_to_related_dictionary"]\
      +" "*48

  return char


def json_to_archive_003(code,j):
  char="%-7s"  % code\
      +" "*24\
      +"%-3s"  % dict_full["003"][j]["cinda_code"]\
      +"%-1s"  % dict_full["003"][j]["area_code"]\
      +"%-3s"  % dict_full["003"][j]["country_code"]\
      +"%-53s" % dict_full["003"][j]["expansion"]\
      +"%-15s" % dict_full["003"][j]["country_for_cinda"]\
      +" "*5

  return char


def json_to_archive_004(code,j):
  char="%-1s"  % code\
      +" "*30\
      +"%-4s"  % dict_full["004"][j]["short_expansion"]\
      +"%3s"   % dict_full["004"][j]["pointer_to_related_dictionary"]\
      +"%-35s" % dict_full["004"][j]["expansion"]\
      +" "*38

  return char


def json_to_archive_005(code,j):
  char="%-6s"  % code\
      +" "*25\
      +"%-4s"  % dict_full["005"][j]["cinda_code"]\
      +"%-1s"  % dict_full["005"][j]["area_code"]\
      +"%-3s"  % dict_full["005"][j]["country_code"]\
      +"%-1s"  % dict_full["005"][j]["additional_area_code"]\
      +"%-3s"  % dict_full["005"][j]["additional_country_code"]\
      +"%-20s" % dict_full["005"][j]["short_expansion"]\
      +"%-48s" % dict_full["005"][j]["expansion"]\

  return char


def json_to_archive_006(code,j):
  char="%-11s" % code\
      +" "*20\
      +"%-7s"  % dict_full["006"][j]["institute_code"]\
      +"%-48s" % dict_full["006"][j]["expansion"]\
      +"%-1s"  % dict_full["006"][j]["cinda_flag"]\
      +" "*24

  return char


def json_to_archive_gen_1(code,j,dict_id):
  char="%-10s" % code\
      +" "*21\
      +"%-53s" % dict_full[dict_id][j]["expansion"]\
      +"%-1s"  % dict_full[dict_id][j]["area_code"]\
      +"%-3s"  % dict_full[dict_id][j]["country_code"]\
      +"%-1s"  % dict_full[dict_id][j]["additional_area_code"]\
      +"%-3s"  % dict_full[dict_id][j]["additional_country_code"]\
      +"%-10s" % dict_full[dict_id][j]["cinda_short_code"]\
      +" "*9

  return char


def json_to_archive_008(code,j):
  char="%3s"   % code\
      +" "*28\
      +"%-2s"  % dict_full["008"][j]["element_symbol"]\
      +"%-20s" % dict_full["008"][j]["element_name"]\
      +" "*58

  return char


def json_to_archive_015(code,j):
  char="%-1s"  % code\
      +" "*30\
      +"%-15s" % dict_full["015"][j]["short_expansion"]\
      +"%-37s" % dict_full["015"][j]["expansion"]\
      +" "*28

  return char


def json_to_archive_016(code,j):
  char="%-5s"  % code\
      +" "*26\
      +"%5s"   % dict_full["016"][j]["internal_numerical_equivalent"]\
      +"%-52s" % dict_full["016"][j]["expansion"]\
      +" "*3\
      +"%-1s"  % dict_full["016"][j]["subentry_number_field_flag"]\
      +" "*19

  return char


def json_to_archive_017(code,j):
  char="%-1s"  % code\
      +" "*30\
      +"%-53s" % dict_full["017"][j]["expansion"]\
      +" "*27

  return char


def json_to_archive_gen_2(code,j,dict_id):
  char="%-5s"  % code\
      +" "*26\
      +"%-53s" % dict_full[dict_id][j]["expansion"]\
      +"%-4s"  % dict_full[dict_id][j]["special_use_flag"]\
      +" "*23

  return char


def json_to_archive_019(code,j):
  char="%-5s"  % code\
      +" "*26\
      +"%-53s" % dict_full["019"][j]["expansion"]\
      +"%-4s"  % dict_full["019"][j]["special_use_flag"]\
      +"%-1s"  % dict_full["019"][j]["delimiter_flag"]\
      +" "*22

  return char


def json_to_archive_gen_3(code,j,dict_id):
  char="%-5s"  % code\
      +" "*26\
      +"%-53s" % dict_full[dict_id][j]["expansion"]\
      +" "*27

  return char


def json_to_archive_024(code,j):
  char="%-10s" % code\
      +" "*21\
      +"%-1s"  % dict_full["024"][j]["data_type_flag_1"]\
      +"%-1s"  % dict_full["024"][j]["data_type_flag_2"]\
      +"%-1s"  % dict_full["024"][j]["family_flag"]\
      +"%-1s"  % dict_full["024"][j]["plotting_flag_1"]\
      +"%-1s"  % dict_full["024"][j]["plotting_flag_2"]\
      +"%-1s"  % dict_full["024"][j]["plotting_flag_3"]\
      +"%-1s"  % dict_full["024"][j]["plotting_flag_4"]\
      +"%-1s"  % dict_full["024"][j]["plotting_flag_5"]\
      +"%-1s"  % dict_full["024"][j]["plotting_flag_6"]\
      +"%-1s"  % dict_full["024"][j]["plotting_flag_7"]\
      +"%-4s"  % dict_full["024"][j]["unit_family_code"]\
      +" "\
      +"%-54s" % dict_full["024"][j]["expansion"]\
      +" "*6\
      +"%-4s"  % dict_full["024"][j]["special_use_flag"]\
      +" "

  return char


def json_to_archive_025(code,j):
  char="%-10s"  % code\
      +" "*21\
      +"%-33s"  % dict_full["025"][j]["expansion"]\
      +" "*2\
      +"%-4s"   % dict_full["025"][j]["unit_family_code"]\

  conversion_factor=dict_full["025"][j]["conversion_factor"]
  if conversion_factor=="":
    char+="           "
  else:
    char+="%11.4E" % conversion_factor

  char+="%-3s"   % dict_full["025"][j]["sorting_flag"]\
      +" "*27

  return char


def json_to_archive_026(code,j):
  char="%-4s" % code\
      +" "*27\
      +"%-2s"  % dict_full["026"][j]["dictionary_24_use"]\
      +"%-2s"  % dict_full["026"][j]["dictionary_25_use"]\
      +"%-2s"  % dict_full["026"][j]["dictionary_236_use"]\
      +"%-50s" % dict_full["026"][j]["expansion"]\
      +" "*24

  return char


def json_to_archive_030(code,j):
  char="%-3s" % code\
      +" "*28\
      +"%10s"  % dict_full["030"][j]["internal_numerical_equivalent"]\
      +"%-55s" % dict_full["030"][j]["expansion"]\
      +"%-4s"  % dict_full["030"][j]["special_use_flag"]\
      +" "*11

  return char


def json_to_archive_031(code,j):
  char="%-5s" % code\
      +" "*26\
      +"%10s"  % dict_full["031"][j]["internal_numerical_equivalent"]\
      +"%-55s" % dict_full["031"][j]["expansion"]\
      +"%-4s"  % dict_full["031"][j]["special_use_flag"]\
      +" "*11

  return char


def json_to_archive_032(code,j):
  char="%-3s" % code\
      +" "*28\
      +"%10s"  % dict_full["032"][j]["internal_numerical_equivalent"]\
      +"%-55s" % dict_full["032"][j]["expansion"]\
      +"%-4s"  % dict_full["032"][j]["special_use_flag"]\
      +" "*11

  return char


def json_to_archive_033(code,j):
  char="%-6s" % code\
      +" "*25\
      +"%6s"   % dict_full["033"][j]["internal_numerical_equivalent_1"]\
      +"%5s"   % dict_full["033"][j]["internal_numerical_equivalent_2"]\
      +"%-1s"  % dict_full["033"][j]["allowed_subfield_flag_1"]\
      +"%-1s"  % dict_full["033"][j]["allowed_subfield_flag_2"]\
      +"%-1s"  % dict_full["033"][j]["allowed_subfield_flag_3"]\
      +"%-1s"  % dict_full["033"][j]["allowed_subfield_flag_4"]\
      +"%-40s" % dict_full["033"][j]["expansion"]\
      +"%-13s" % dict_full["033"][j]["nuclide_code"]\
      +" "*12

  return  char


def json_to_archive_034(code,j):
  char="%-5s" % code\
      +" "*26\
      +"%10s"  % dict_full["034"][j]["internal_numerical_equivalent"]\
      +"%-5s"  % dict_full["034"][j]["general_quantity_modifier_flag"]\
      +"%-55s" % dict_full["034"][j]["expansion"]\
      +"%-4s"  % dict_full["034"][j]["special_use_flag"]\
      +" "*6

  return  char


def json_to_archive_035(code,j):
  char="%-5s" % code\
      +" "*26\
      +"%10s"  % dict_full["035"][j]["internal_numerical_equivalent"]\
      +"%-40s" % dict_full["035"][j]["expansion"]\
      +" "*30

  return  char


def json_to_archive_043(code,j):
  char="%2s"   % code\
      +" "*29\
      +"%-55s" % dict_full["043"][j]["expansion"]\
      +" "*25

  return char


def json_to_archive_045(code,j):
  char="%-3s"  % code\
      +" "*28\
      +"%-3s"  % dict_full["045"][j]["web_quantity_code"]\
      +" "*4\
      +"%-48s" % dict_full["045"][j]["expansion"]\
      +" "*25

  return char


def json_to_archive_047(code,j):
  char="%-3s"  % code\
      +" "*28\
      +"%-10s" % dict_full["047"][j]["cinda_reaction_code"]\
      +"%-3s"  % dict_full["047"][j]["cinda_quantity_code"]\
      +" "*2\
      +"%-1s"  % dict_full["047"][j]["flag"]\
      +" "*64

  return char


def json_to_archive_048(code,j):
  char="%-5s"  % code\
      +" "*26\
      +"%-10s" % dict_full["048"][j]["short_expansion"]\
      +"%-45s" % dict_full["048"][j]["expansion"]\
      +" "*25

  return char


def json_to_archive_049(code,j):
  char="%-8s"  % code\
      +" "*23\
      +"%-1s" % dict_full["049"][j]["media_type"]\
      +"%-1s" % dict_full["049"][j]["media_type_for_alternative_ISSN"]\
      +"%-1s" % dict_full["049"][j]["doi_registerer_identifier"]\
      +"%-1s" % dict_full["049"][j]["range_type_identifier"]\
      +" "\
      +"%-8s" % dict_full["049"][j]["alternative_ISSN"]\
      +" "\
      +"%-6s" % dict_full["049"][j]["reference_code_1"]\
      +"%5s" % dict_full["049"][j]["lower_boundary_of_range_1"]\
      +"%5s" % dict_full["049"][j]["upper_boundary_of_range_1"]\
      +"%-6s" % dict_full["049"][j]["reference_code_2"]\
      +"%5s" % dict_full["049"][j]["lower_boundary_of_range_2"]\
      +"%5s" % dict_full["049"][j]["upper_boundary_of_range_2"]\
      +"%-6s" % dict_full["049"][j]["reference_code_3"]\
      +"%5s" % dict_full["049"][j]["lower_boundary_of_range_3"]\
      +"%5s" % dict_full["049"][j]["upper_boundary_of_range_3"]\
      +"%-6s" % dict_full["049"][j]["reference_code_4"]\
      +"%5s" % dict_full["049"][j]["lower_boundary_of_range_4"]\
      +"%5s" % dict_full["049"][j]["upper_boundary_of_range_4"]\
      +" "*2

  return char


def json_to_archive_052(code,j):
  char="%-2s"  % code\
      +" "*29\
      +"%-55s" % dict_full["052"][j]["expansion"]\
      +" "*5\
      +"%-15s" % dict_full["052"][j]["country"]\
      +" "*5

  return char


def json_to_archive_113(code,j):
  char="%-3s"  % code\
      +" "*28\
      +"%-55s" % dict_full["113"][j]["expansion"]\
      +" "*25

  return char


def json_to_archive_144(code,j):
  char="%-13s" % code\
      +" "*18\
      +"%-1s"  % dict_full["144"][j]["area_code"]\
      +"%-3s"  % dict_full["144"][j]["country_code"]\
      +"%-1s"  % dict_full["144"][j]["additional_area_code"]\
      +"%-3s"  % dict_full["144"][j]["additional_country_code"]\
      +"%-52s" % dict_full["144"][j]["expansion"]\
      +" "*20

  return char


def json_to_archive_209(code,j):
  code_out=code.strip()
  arrays=code.split("-")
  if float(arrays[0])<10:
    code_out="  "+code_out
  elif float(arrays[0])<100:
    code_out=" "+code_out

  char="%-10s" % code_out\
      +" "*21\
      +"%-5s"  % dict_full["209"][j]["cinda_code"]\
      +"%7s"   % dict_full["209"][j]["internal_numerical_equivalent_1"]\
      +"%7s"   % dict_full["209"][j]["internal_numerical_equivalent_2"]\
      +" "*21\
      +"%-25s" % dict_full["209"][j]["expansion"]\
      +" "*6\
      +" "*9

  return char


def json_to_archive_213(code,j):
  char="%-4s" % code\
      +" "*27\
      +"%-3s"  % dict_full["213"][j]["cinda_quantity_code"]\
      +" "*2\
      +"%-3s"  % dict_full["213"][j]["web_quantity_code"]\
      +" "\
      +"%2s"   % dict_full["213"][j]["sorting_flag"]\
      +" "\
      +"%-1s"  % dict_full["213"][j]["independent_variable_family_flag_1"]\
      +" "\
      +"%-1s"  % dict_full["213"][j]["independent_variable_family_flag_3"]\
      +"%-1s"  % dict_full["213"][j]["independent_variable_family_flag_4"]\
      +"%-1s"  % dict_full["213"][j]["independent_variable_family_flag_5"]\
      +"%-1s"  % dict_full["213"][j]["independent_variable_family_flag_6"]\
      +"%-1s"  % dict_full["213"][j]["independent_variable_family_flag_7"]\
      +" "\
      +" "\
      +" "\
      +"%-46s" % dict_full["213"][j]["expansion"]\
      +" "*12

  return char


def json_to_archive_227(code,j):

  code_out=code.strip()
  arrays=code.split("-")
  if float(arrays[0])<10:
    code_out="  "+code_out
  elif float(arrays[0])<100:
    code_out=" "+code_out

  char="%-13s" % code_out\
      +" "*24\
      +"%7s"    % dict_full["227"][j]["internal_numerical_equivalent"]\
      +"%-1s"   % dict_full["227"][j]["use_flag"]\
      +"%-6s"   % dict_full["227"][j]["spin_and_parity"]\
      +"%-1s"   % dict_full["227"][j]["state_ordering_flag"]\

  half_life=dict_full["227"][j]["half-life"]
  if half_life=="":
    char+="           "
  else:
    char+="%11.4E" % half_life

  char+="%-1s"   % dict_full["227"][j]["decay_flag"]

  char+="%-1s"   % dict_full["227"][j]["mass_flag"]

  char+="%-1s"   % dict_full["227"][j]["energy_flag"]

  isotopic_abundance=dict_full["227"][j]["isotopic_abundance"]
  if isotopic_abundance=="":
    char+="           "
  else:
    char+="%11.4E" % isotopic_abundance

  atomic_weight=dict_full["227"][j]["atomic_weight"]
  if atomic_weight=="":
    char+="            "
  else:
    if atomic_weight<10:
      atomic_weight="%.10f" % atomic_weight
    elif atomic_weight<100:
      atomic_weight="%.9f" % atomic_weight
    else:
      atomic_weight="%.8f" % atomic_weight
    char+=atomic_weight

  excitation_energy=dict_full["227"][j]["excitation_energy"]
  if excitation_energy=="":
    char+="            "
  else:
    excitation_energy="%12.6f" % excitation_energy
    char+=excitation_energy

  char+="%-10s"  % dict_full["227"][j]["explanation"]

  return char


def json_to_archive_235(code,j):
  char="%-1s"  % code\
      +" "*30\
      +"%-4s"  % dict_full["235"][j]["short_expansion"]\
      +" "*2\
      +"%-35s" % dict_full["235"][j]["expansion"]\
      +" "*39

  return char


def json_to_archive_236(code,j):
  char="%-30s" % code\
      +" "\
      +"%-3s"  % dict_full["236"][j]["reaction_type_code"]\
      +" "\
      +"%-4s"  % dict_full["236"][j]["unit_family_code"]\
      +"%-1s"  % dict_full["236"][j]["resonance_flag"]\
      +"%-71s" % dict_full["236"][j]["expansion"]\

  return char


def json_to_archive_top(code,j):
  code_out=code
  code_out=re.sub("^00", '  ', code_out);
  code_out=re.sub("^0", ' ', code_out);
  char="%-3s"  % code_out\
      +" "\
      +"%-30s" % dict_full["950"][j]["dictionary_name"]\
      +" "\
      +"%2s"   % dict_full["950"][j]["number_of_daniel_keys"]\
      +" "\
      +"%-44s" % dict_full["950"][j]["formats_of_key_and_expansion_fields"]\
      +" "*41

  return char


def print_long_expansion_archive(f,long_expansion,j,dict_id):
  long_expansion="("+long_expansion+")"
  chars=list(long_expansion)

  char0="%-1s"  % dict_full[dict_id][j]["alteration_flag"]\
       +"%-3s"  % dict_full[dict_id][j]["status_code"]\
       +" "*8\
       +" "*30\

  text=char0+" "
  text1=char0+" "

  if dict_id=="236":
    len_max=87
  else:
    len_max=98

  for i,char in enumerate(chars):
    text+=char
    text1+=char
    if len(text)>len_max:
      text0="%-123s" % text0
      f.write(text0+"\n")
      text=text1
    elif i==len(chars)-1:
      text="%-123s" % text
      f.write(text+"\n")
      text=""
    elif chars[i+1]==" ":
      text0=text
      text1=char0+" "

  if len(text)!=0: # last line
    text="%-123s" % text
    f.write(text+"\n")

  return


def get_code(dict_id,record):
  primary_key=get_primary_key(dict_id)
  code=record[primary_key]

  return code


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
   usage="Convert JSON Dictionary to Archive Dictionaries",\
   epilog="example: x4_dicj2a.py -n 9132 -i json -o output")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-n", "--dict_ver",\
   help="dictionary version (transmission ID)")
  parser.add_argument("-i", "--dir_json",\
   help="directory of input JSON Dictionary")
  parser.add_argument("-o", "--dir_archive",\
   help="directory of output Archive Dictionaries")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("DICJ2A (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force
  dict_ver=args.dict_ver
  if dict_ver is None:
    dict_ver=input("dictionary version [9132] -------------------------> ")
    if dict_ver=="":
      dict_ver="9132"
  if not re.compile(r"^9\d{3,3}$").search(dict_ver):
    print(" ** Dictionary version must be a 4-digit integer starting from 9.")
  while not re.compile(r"^\d{4,4}$").search(dict_ver):
    dict_ver=input("dictionary version [9132] -------------------------> ")
    if dict_ver=="":
      dict_ver="9132"
    if not re.compile(r"^9\d{3,3}$").search(dict_ver):
      print(" ** Dictionary version must be a 4-digit integer starting from 9.")

  dir_json=args.dir_json
  if dir_json is None:
    dir_json=input("directory of input JSON Dictionary [json] ---------> ")
    if dir_json=="":
      dir_json="json"
  file_in=dir_json+"/dict_"+dict_ver+".json"
  if not os.path.isfile(file_in):
    print(" ** JSON Dictionary "+file_in+" does not exist.")
  while not os.path.isfile(file_in):
    dir_json=input("directory of input JSON Dictionary [json] ---------> ")
    if dir_json=="":
      dir_json="json"
    file_in=dir_json+"/dict_"+dict_ver+".json"
    if not os.path.isfile(file_in):
      print(" ** JSON Dictionary "+file_in+" does not exist.")

  dir_archive=args.dir_archive
  if dir_archive is None:
    dir_archive=input("directory of output Archive Dictionaries [output] -> ")
  if dir_archive=="":
    dir_archive="output"

  if os.path.isdir(dir_archive):
    msg="Directory '"+dir_archive+"' exists and must be overwritten."
    print_error(msg,"",force0)
  else:
    msg="Directionry '"+dir_archive+"' does not exist and must be created."
    print_error(msg,"",force0)
    os.mkdir(dir_archive)

  return dict_ver,dir_json,dir_archive,force0


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
  dicj2a() 
  exit()
