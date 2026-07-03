#!/usr/bin/python3
ver="2026.06.24"
############################################################
# J4VIEW Ver.2026.06.24
# (Utility to convert J4 to HTML)
#
# Naohiko Otuka (IAEA Nuclear Data Section)
############################################################
import argparse
import datetime
import glob
import json
import os
import re
import time

def j4view():
  args=get_args(ver)
  main(*get_input(args))


def main(dir_j4,file_dict,file_css,entry,file_html,force0,gothi0,unfor0,limit0):
  time_start=time.time()

  global force
  global gothi
  global dict_json
  global unfor
  global limit

  force=force0
  gothi=gothi0
  unfor=unfor0
  limit=limit0

  entry=entry.lower()
  pattern=dir_j4+"/"+entry+".[0-9][0-9][0-9]*.json"
  all_files=glob.glob(pattern)
  files = [file for file in all_files if re.search(r"\d\d\d(\.[A-Z1-9])?", file)]
  files=sorted(files)

  dict_json=read_dict(file_dict)

  f=open(file_html,"w")
  print_head(f,entry,file_css)

  for nfile, file_j4 in enumerate(files):
    m=re.search(r"(\d\d\d)(\.[A-Z1-9])?\.json", file_j4)
    if m.groups()[1] is None:
      pointer=""
    else:
      pointer=m.groups()[1][1]

    x4_json=read_x4json(file_j4)

    if x4_json["title"]=="J4 - EXFOR in JSON, number as string without pointer with common subentry" or\
       x4_json["title"]=="J4 - EXFOR in JSON without pointer with common subentry":
      respar=False
    elif x4_json["title"]=="J4 - EXFOR in JSON, number as string (resonance parameter)" or\
         x4_json["title"]=="J4 - EXFOR in JSON (resonance parameter)":
      respar=True
    else:
      msg="The input JSON EXFOR file must be the one processed by POIPOI with option -c."
      print_error_fatal(msg,x4_json["title"])

    keywords=["TRANS","MASTER","REQUEST","ENTRY"]
    for keyword in keywords:
      if keyword in x4_json:
        msg="Input file should not contain "+keyword+ "record.\n"
        print_error_fatal(msg,"")
   
    if keyword=="ENTRY":
      if nfile==0:
        out_common=True
      else:
        out_common=False

      print_entry(f,x4_json["entries"][0],out_common,nfile,pointer,respar)

  print_foot(f)
  f.close()

  time_end=time.time()
  time_elapsed=format(time_end-time_start, ".2f")
  print("J4VIEW: Processing terminated normally. "+time_elapsed+" sec.\n")


def print_head(f,entry,file_css):
  f.write("<!DOCTYPE html>\n")
  f.write("<html lang='en'>\n")
  f.write("<head>\n")
  f.write("<meta http-equiv='Content-Type' content='text/html; charset=UTF-8'>\n")
  f.write("<style>\n")

  lines=get_file_lines(file_css)
  for line in lines:
    if re.compile("XXX").search(line):
      if gothi:
        line=re.sub("XXX","sans-serif",line)
      else:
        line=re.sub("XXX","serif",line)
    f.write(line)

  entry=entry.upper()
  f.write("</style>\n")
  f.write("<title>\n")
  f.write("EXFOR "+entry+"\n")
  f.write("</title>\n")
  f.write("<script>\n")
  f.write("function toggleDetails(){\n")
  f.write("  const detailsElements = document.querySelectorAll('details');\n")
  f.write("  const isOpen = detailsElements[0].open;\n")
  f.write("  detailsElements.forEach(details=>{\n")
  f.write("  details.open = !isOpen;\n")
  f.write("  });\n")
  f.write("}\n")
  f.write("</script>\n")
  f.write("</head>\n")
  f.write("<body>\n")

  return


def print_foot(f):
  f.write("</body>\n")
  f.write("</html>\n")

  return


def print_entry(f,x4_json,out_common,nfile,pointer,respar):
  if out_common:
    f.write("<div class='ENTRY'>\n")
    f.write("EXFOR "+x4_json["ENTRY"]["N1"]+"\n")
    date=print_date(x4_json["ENTRY"]["N2"],0)
    f.write("<br>\n<data value='"+date+"'>\n")
    f.write("last update: "+date+"\n")
    f.write("</data>\n")

    if x4_json["ENTRY"]["transmission_identification"]!=None:
      trans=x4_json["ENTRY"]["transmission_identification"]
      f.write("<br>\n<data value='"+trans+"'>\n")
      f.write("last transmission: "+trans+"\n")
      f.write("</data>\n")

    f.write("</div>\n")
    f.write("<div class='openclose'>\n")
    f.write("<a href='javascript:toggleDetails();'>open / close all</a>\n")
    f.write("</div>\n")

  for nsubent, subentry in enumerate(x4_json["subentries"]):

    if out_common or nsubent!=0:
      print_subent(f,x4_json["subentries"][nsubent],nfile,pointer,respar)

  return


def print_subent(f,x4_json,nfile,pointer,respar):
  keywords=["SUBENT","ENDSUBENT","NOSUBENT",\
            "BIB","ENDBIB","NOBIB",\
            "ENDCOMMON","NOCOMMON",\
            "ENDDATA","NODATA"]

  for keyword in x4_json:

    if keyword in keywords:

      if keyword=="SUBENT" or keyword=="NOSUBENT":
        char=x4_json[keyword]["N1"]
        an=char[0:5]
        san=char[5:8]

        if san=="001":
          num=0
        else:
          num=nfile+1

        f.write("<details name='"+str(num)+"'>\n")
        f.write("<summary>\n")

        if san=="001":
          f.write(str(num)+". OVERALL DESCRIPTION ("+an+".001)\n")
        else:
          if keyword=="NOSUBENT":
            char=" (deleted)"
          else:
            char=""
          if pointer=="":
            f.write(str(num)+". DATA TABLE "+an+"."+san+char+"\n")
          else:
            f.write(str(num)+". DATA TABLE "+an+"."+san+"."+pointer+char+"\n")

        date=print_date(x4_json[keyword]["N2"],0)
        f.write("<br>\n<data value='"+date+"'>\n")
        f.write("last update: "+date+"\n")
        f.write("</data>\n")

        if x4_json[keyword]["transmission_identification"]!=None:
          trans=x4_json[keyword]["transmission_identification"]
          f.write("<br>\n<data value='"+trans+"'>\n")
          f.write("last transmission: "+trans+"\n")
          f.write("</data>\n")

        f.write("</summary>\n")

      elif keyword=="ENDSUBENT":
        f.write("</details>\n")

      elif keyword=="BIB":
        f.write("<div class='BIB'>\n")

      elif keyword=="ENDBIB":
        f.write("</div>\n")

    elif keyword=="COMMON":
      print_common_data(f,keyword,x4_json["COMMON"])

    elif keyword=="DATA":
      print_common_data(f,keyword,x4_json["DATA"])

    else:
      print_bib(f,keyword,x4_json,respar)

  return


def print_bib(f,keyword,x4_json,respar):
  table_keywords=["ANG-SEC", "EN-SEC", "MOM-SEC", "DECAY-DATA", "DECAY-MON", "FLAG",\
                  "ERR-ANALYS", "HISTORY", "LEVEL-PROP", "INC-SPECT", "MISC-COL"]

  f.write("<header>\n")
  expansion=dict_retrieval("002", "keyword", keyword, "expansion")
  f.write(expansion+"\n")
  f.write("</header>\n")

  table_out=False

  x4_json_keyword=x4_json[keyword]
  pointers=list(dict.fromkeys([x["pointer"] for x in x4_json_keyword]))
  for pointer in pointers:
    for i, item in enumerate(x4_json_keyword):
      first_text=""
      if item["pointer"]==pointer:
        if pointer!="" and respar: # resonance parameter
          if keyword not in table_keywords:
            f.write("<div class='pointer'>\n")
            f.write("Parameter #"+pointer)
            f.write("</div>\n")
              
        if keyword=="ANG-SEC" or\
           keyword=="EN-SEC" or\
           keyword=="HALF-LIFE" or\
           keyword=="MOM-SEC":

          expansions=[]
          free_texts=[]

          if item["coded_information"] is not None:
            code=item["coded_information"]["heading"]
            nuclide=conv_nuclpart(item["coded_information"]["particle"],1)
            expansions.append(nuclide)

            aligns=["L","L"]
            free_texts=item["free_text"]
            table_out=print_table(f,keyword,code,expansions,aligns,0,0,free_texts,table_out,pointer,respar)

        elif keyword=="ASSUMED":
          if item["coded_information"] is not None:
            prefix=item["coded_information"]["heading"]
            result=""
            coded_information=item["coded_information"]["reaction"]
            f.write("<div class='expansion'>\n")
            print_code_combination(f,keyword,prefix,result,coded_information)
            f.write("</div>\n")


        elif keyword=="DECAY-DATA":
          if item["coded_information"] is not None:
            table_out=print_decaydata(f,keyword,item["coded_information"],item["free_text"],table_out,pointer,respar)


        elif keyword=="DECAY-MON":
          if item["coded_information"] is not None:
            table_out=print_decaydata(f,keyword,item["coded_information"],item["free_text"],table_out,pointer,respar)


        elif keyword=="ERR-ANALYS":

          expansions=[]
          free_texts=[]

          if item["coded_information"] is None:
            code=""
            expansions.append("")
            expansions.append("")
            expansions.append(None)
          else:
            code=item["coded_information"]["heading"]

            if item["coded_information"]["minimum_value"] is None:
              expansions.append("")
            else:
              expansions.append(str(item["coded_information"]["minimum_value"]))
           
            if item["coded_information"]["maximum_value"] is None:
              expansions.append("")
            else:
              expansions.append(str(item["coded_information"]["maximum_value"]))
           
            if item["coded_information"]["correlation_property"]=="F":
              expansions.append("Fully correlated")
            elif item["coded_information"]["correlation_property"]=="C":
              expansions.append("Correlated")
            elif item["coded_information"]["correlation_property"]=="U":
              expansions.append("Uncorrelated")
            else:
              expansions.append(None)

          aligns=["L","R","R","L"]
          free_texts=item["free_text"]
          table_out=print_table(f,keyword,code,expansions,aligns,0,0,free_texts,table_out,pointer,respar)


        elif keyword=="FACILITY":
          if item["coded_information"] is not None:

            if item["coded_information"]["institute"] is not None:

              facility=dict_retrieval("018","code",item["coded_information"]["facility"][0],"expansion")
              institute=dict_retrieval("003","code",item["coded_information"]["institute"],"expansion")

              f.write("<div class='expansion'>\n")
              f.write(facility+" of "+institute+"\n")
              f.write("</div>\n")

            else:
              print_code(f,keyword,item["coded_information"]["facility"])


        elif keyword=="FLAG" or keyword=="INC-SPECT" or keyword=="MISC-COL":

          expansions=[]
          free_texts=[]

          if item["coded_information"] is not None:

            code=item["coded_information"][0]
            if keyword=="FLAG":
              code=str(code)
           
            aligns=["L"]
            free_texts=item["free_text"]
            table_out=print_table(f,keyword,code,expansions,aligns,0,0,free_texts,table_out,pointer,respar)


        elif keyword=="HALF-LIFE":
          if item["coded_information"] is not None:

            f.write("("+item["coded_information"]["heading"]+",")
            f.write(item["coded_information"]["nuclide"]+")")


        elif keyword=="HISTORY":

          expansions=[]
          free_texts=[]

          date=print_date(item["coded_information"]["date"],0)
          expansions.append(date)
          if item["coded_information"]["history"] is not None:
            expansion=dict_retrieval("015","code",item["coded_information"]["history"],"expansion")
            expansions.append(expansion)
          else:
            expansions.append(None)

          aligns=["","L","L"]
          free_texts=item["free_text"]
          table_out=print_table(f,keyword,"nocode",expansions,aligns,0,0,free_texts,table_out,pointer,respar)


        elif keyword=="INC-SOURCE":
          if item["coded_information"] is not None:
            if item["coded_information"]["reaction"] is not None:
              f.write("("+item["coded_information"]["incident_source"][0]+"=("+\
                          item["coded_information"]["reaction"]["code"]+"))")
            else:
              print_code(f,keyword,item["coded_information"]["incident_source"])


        elif keyword=="LEVEL-PROP":

          expansions=[]
          free_texts=[]

          if item["coded_information"] is not None:
            if item["coded_information"]["flag"] is not None:
              code=str(item["coded_information"]["flag"])
            else:
              code=""

            nuclide=conv_nuclpart(item["coded_information"]["nuclide"],1)
            expansions.append(nuclide)

            if item["coded_information"]["level_identification"] is not None:
              field_identifier=item["coded_information"]["level_identification"]["field_identifier"]
              expansions.append(field_identifier)
              if re.compile(r"LVL-NUMB|IAS-NUMB").search(field_identifier):
                value=(str(item["coded_information"]["level_identification"]["value"]))
              else:
                value=(str(item["coded_information"]["level_identification"]["value"])+" MeV")
              expansions.append(value)
            else:
              expansions.append("")
              expansions.append("")

            if item["coded_information"]["level_properties"] is not None:
              spin=""
              parity=""
              for property in item["coded_information"]["level_properties"]:
                if property["field_identifier"]=="SPIN":
                  spins=[]
                  for spin in property["value"]:
                    spin=float(spin)
                    if int(spin)!=spin:
                      spin=str(int(spin*2))
                      spin=spin+"/2"
                    else:
                      spin=str(int(spin))
                    spins.append(spin)
                  spin=" or ".join(spins)
                elif property["field_identifier"]=="PARITY":
                  parities=[]
                  for parity in property["value"]:
                    if float(parity)==1:
                      parity="+"
                    elif float(parity)==-1:
                      parity="-"
                    else:
                      parity="?"
                    parities.append(parity)
                  parity=" or ".join(parities)
              expansions.append(spin+"<sup>"+parity+"</sup>")
            else:
              expansions.append("")
              expansions.append("")

          aligns=["R","L","L","R","L"]
          free_texts=item["free_text"]
          table_out=print_table(f,keyword,code,expansions,aligns,0,0,free_texts,table_out,pointer,respar)


        elif keyword=="MONITOR":
          if item["coded_information"] is not None:
            if item["coded_information"]["heading"] is not None:
              prefix=item["coded_information"]["heading"]
            else:
              prefix=""
            result=""
            coded_information=item["coded_information"]["reaction"]
            f.write("<div class='expansion'>\n")
            print_code_combination(f,keyword,prefix,result,coded_information)
            f.write("</div>\n")


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
            result=""
            f.write("<div class='expansion'>\n")
            print_code_combination(f,keyword,prefix,result,coded_information)
            f.write("</div>\n")


        elif keyword=="REACTION":
          coded_information=item["coded_information"]
          prefix=""
          if "RESULT" in x4_json:
            result=x4_json["RESULT"][0]["coded_information"][0]
          else:
            result=""
          f.write("<div class='expansion'>\n")
          print_code_combination(f,keyword,prefix,result,coded_information)
          f.write("</div>\n")
                  

        elif keyword=="MONIT-REF" or keyword=="REL-REF":

          if keyword=="MONIT-REF":
           if item["coded_information"]["heading"] is not None:
             f.write("<code>\n")
             f.write(item["coded_information"]["heading"]+": \n")
             f.write("</code>\n")

          if item["coded_information"] is not None:
            if item["coded_information"]["subentry_number"] is not None:
              subentry_number=item["coded_information"]["subentry_number"]
            else:
              subentry_number=""
            if item["coded_information"]["author"] is not None:
              author=item["coded_information"]["author"]
            else:
              author=""

            f.write("<div class='expansion'>\n")
            print_reference(f,subentry_number,author,item["coded_information"]["reference"])
            f.write("</div>\n")
           
            
          if keyword=="REL-REF":
            if item["coded_information"]["code"]!="N":
              first_text=dict_retrieval("017","code",item["coded_information"]["code"],"expansion")


        elif keyword=="SAMPLE":
          if item["coded_information"] is not None:
            f.write("<div class='expansion'>\n")
            nuclide=conv_nuclpart(item["coded_information"]["nuclide"],0)
            enrichment=str(item["coded_information"]["value"])
            f.write(nuclide)
            if item["coded_information"]["field_identifier"]=="ENR":
              f.write(" enriched to "+enrichment)
            elif item["coded_information"]["field_identifier"]=="NAT":
              f.write(" with natural isotopic abundance of "+enrichment)
            f.write("</div>\n")

        elif keyword=="STATUS":

          if item["coded_information"] is not None:

            if item["coded_information"]["subentry_number"] is not None:
              expansion=dict_retrieval("016","code",item["coded_information"]["status"][0],"expansion")
              f.write("<div class='expansion'>\n")
              f.write(expansion)
              an=item["coded_information"]["subentry_number"][0:5]
              san=item["coded_information"]["subentry_number"][5:8]
              if san=="001":
                f.write(" (See <a href=\"https://nds.iaea.org/EXFOR/"+an+"\" target=\"_blank\">EXFOR "+an+"</a>)\n")
              else:
                f.write(" (See <a href=\"https://nds.iaea.org/EXFOR/"+an+"."+san+"\" target=\"_blank\">EXFOR "+an+"."+san+"</a>)\n")
              f.write("</div>\n")

            elif item["coded_information"]["author"] is not None:
              expansion=dict_retrieval("016","code",item["coded_information"]["status"][0],"expansion")
              f.write("<div class='expansion'>\n")
              f.write(expansion)
              author=item["coded_information"]["author"]
              f.write(" (Ref. ")
              print_reference(f,"",author,item["coded_information"]["reference"])
              f.write(")")
              f.write("</div>\n")

            else:
              print_code(f,keyword,item["coded_information"]["status"])

        else:

          if item["coded_information"] is not None:
            print_code(f,keyword,item["coded_information"])
          

        if not table_out:
          if first_text!="":
            item["free_text"].insert(0,"["+first_text+"]")
          if item["free_text"]!=[""]:
            print_free_text(f,keyword,item["free_text"])

  if table_out:
    f.write("</tbody>\n") 
    f.write("</table>\n")

  return


def print_common_data(f,keyword,x4_json):
  f.write("<div class='DATA'>\n")
  f.write("<header>\n")
  if keyword=="COMMON":
    f.write("Constants\n")
  else:
    npts=x4_json["N2"]
    if limit!=-1 and npts>limit*2:
      f.write("Data table (only first and last "+str(limit)+" data points are shown)\n")
    else:
      f.write("Data table\n")
  f.write("</header>\n")
  f.write("<pre>\n")

  nfields=x4_json["N1"]
  hline="------------"*nfields 
  f.write(hline+"\n")

  for i, pointer in enumerate (x4_json["pointer"]):
    if pointer=="":
      pointer_out=" "
    else:
      pointer_out=pointer
    f.write("%-11s"  % x4_json["heading"][i])
    f.write(pointer_out)
  f.write("\n")
    
  for i, pointer in enumerate (x4_json["pointer"]):
    f.write("%-12s"  % x4_json["unit"][i])
  f.write("\n")

  f.write(hline+"\n")

  if keyword=="COMMON":
    for i, pointer in enumerate (x4_json["pointer"]):
      f.write("%-12s"  % x4_json["value"][i])
    f.write("\n")

  elif keyword=="DATA":
    for j, line in enumerate (x4_json["value"]):
      if (j<limit or j>npts-limit-1) or limit==-1:
        for i, pointer in enumerate (x4_json["pointer"]):
          if x4_json["value"][j][i] is None:
            f.write("%-12s"  % " ")
          else:
            f.write("%-12s"  % x4_json["value"][j][i])
        f.write("\n")

      elif j==limit and limit!=-1:
        for i, pointer in enumerate (x4_json["pointer"]):
          f.write(" .......... ")
        f.write("\n")


  f.write(hline+"\n")
  f.write("</pre>\n")
  f.write("</div>\n")
  return


def print_code(f,keyword,codes):
  expansions=[]
  if keyword=="AUTHOR" or keyword=="EXP-YEAR":
    f.write("<div class='author'>\n")
    for j, code in enumerate(codes):
      expansions.append(str(code))
    char=", ".join(expansions)
    f.write(char+"\n")
    f.write("</div>\n")

  elif keyword=="INSTITUTE":
    for j, code in enumerate(codes):
      expansion=dict_retrieval("003","code",code,"expansion")
      if code[1:4]=="ZZZ":
        country=dict_retrieval("003","code",code,"country_for_cinda")
      else:
        if code[3:4]==" ":
          code_country=code[0:4]+code[1:3]
        else:
          code_country=code[0:4]+code[1:4]
        country=dict_retrieval("003","code",code_country,"expansion")
      f.write("<div class='institute'>\n")
      if code[1:4]=="ZZZ":
        f.write(expansion+", "+country+"\n")
      elif code==code_country:
        f.write(country+"\n")
      else:
        f.write(expansion+", "+country+"\n")
      f.write("</div>\n")

  elif keyword=="PART-DET":
    f.write("<div class='expansion'>\n")
    for j, code in enumerate(codes):
      expansions.append(conv_nuclpart(code,1))
    char=", ".join(expansions)
    f.write(char+"\n")
    f.write("</div>\n")

  else:
    f.write("<div class='expansion'>\n")
    for code in codes:
      num=dict_retrieval("002","keyword",keyword,"pointer_to_related_dictionary")
      if num<10:
        num="00"+str(num)
      elif num<100:
        num="0"+str(num)
      else:
        num=str(num)
      expansion=dict_retrieval(num,"code",code,"expansion")
      expansions.append(expansion)
    char=", ".join(expansions)
    f.write(char+"\n")
    f.write("</div>\n")


  return


def print_code_combination(f,keyword,prefix,result,coded_information):

  if prefix!="":
    f.write("<code>\n")
    f.write(prefix+": \n")
    f.write("</code>\n")


  if coded_information["unit_combination"]=="(%)":
    if keyword=="REFERENCE":
      print_reference(f,"","",coded_information["code_unit"][0])
      f.write("\n")

    else:
      print_reaction(f,coded_information["code_unit"][0]["field"])
      f.write("\n")

  elif coded_information["unit_combination"]=="((%)=(%))":
    if keyword=="REFERENCE":
      print_reference(f,"","",coded_information["code_unit"][0])
      f.write("[alias: ")
      print_reference(f,"","",coded_information["code_unit"][1])
      f.write("]\n")

    else:
      print_reaction(f,coded_information["code_unit"][0]["field"])
      f.write("[alias: ")
      print_reaction(f,coded_information["code_unit"][1]["field"])
      f.write("]\n")


  elif coded_information["unit_combination"]=="((%)/(%))":
    f.write("Ratio of ")
    print_reaction(f,coded_information["code_unit"][0]["field"])
    f.write(" to ")
    print_reaction(f,coded_information["code_unit"][1]["field"])
    f.write("\n")

  elif coded_information["unit_combination"]=="((%)*(%))":
    f.write("Product of ")
    print_reaction(f,coded_information["code_unit"][0]["field"])
    f.write(" and ")
    print_reaction(f,coded_information["code_unit"][1]["field"])
    f.write("\n")

  elif coded_information["unit_combination"]=="((%)+(%))":
    f.write("Sum of ")
    print_reaction(f,coded_information["code_unit"][0]["field"])
    f.write(" and ")
    print_reaction(f,coded_information["code_unit"][1]["field"])
    f.write("\n")

  elif coded_information["unit_combination"]=="((%)-(%))":
    f.write("Difference between")
    print_reaction(f,coded_information["code_unit"][0]["field"])
    f.write(" and ")
    print_reaction(f,coded_information["code_unit"][1]["field"])
    f.write("\n")

  elif result=="RVAL":
    f.write("R-value of ")
    print_reaction(f,coded_information["code_unit"][0]["field"])
    f.write("relative to ")
    print_reaction(f,coded_information["code_unit"][2]["field"])
    f.write("with ")
    char=conv_nuclpart(coded_information["code_unit"][1]["field"]["product"],0)
    f.write(char)
    f.write(" as the monitor product")

  else:
    chars=list(coded_information["unit_combination"])
    code_out=prefix
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

  return


def print_free_text(f,keyword,texts):

# outmod
# 0: normal free text
# 1: paragraph
# 2: heading line
# 3.1: item (level 1)
# 3.2: item (level 2)
# 4: table
# 5: covariance

  keyword_table=["ANG-SEC", "EN-SEC", "HALF-LIFE", "MOM-SEC",
                 "ERR-ANALYS",
                 "FLAG", "INC-SPECT", "MISC-COL",
                 "HISTORY",
                 "LEVEL-PROP"]

  outmod=0

  if unfor:
    f.write("<div class='freetext'>\n")
    for text in texts:

      text=replace_free_text(text)

      if re.search(r"^ \((X|Y|Z|XY|ZP)", text) and keyword=="COVARIANCE":
        if outmod==0:
          outmod=5
          f.write("<pre>\n")

      f.write(text+"\n")

    if outmod==5:
      f.write("</pre>\n")
    f.write("</div>\n")

    return


  f.write("<div class='freetext'>\n")
  char_bullet=""
  for j,text in enumerate(texts):

    text=replace_free_text(text)

    if j==0:
      outmod=0

    if re.search(r"^\w", text): # a paragraph (col.11 = [A-Za-z0-9_])
      if outmod==0:
        outmod=1
      elif outmod==1 or outmod==2:
        if keyword not in keyword_table:
          f.write("</p>\n")
        outmod=1
      elif outmod==3.1:
        f.write("</li>\n")
        f.write("</ul>\n")
        outmod=1
      elif outmod==3.2:
        f.write("</li>\n")
        f.write("</ul>\n")
        f.write("</li>\n")
        f.write("</ul>\n")
        outmod=1

      if outmod!=4 and outmod!=5:
        if keyword not in keyword_table:
          f.write("<p>\n")
      f.write(text+"\n")

    elif re.search(r"^\*", text): # heading line (col.11 = *)
      if outmod==0:
        outmod=2
      elif outmod==1 or outmod==2:
        if keyword not in keyword_table:
          f.write("</p>\n")
        outmod=2
      elif outmod==3.1:
        f.write("</li>\n")
        f.write("</ul>\n")
        outmod=2
      elif outmod==3.2:
        f.write("</li>\n")
        f.write("</ul>\n")
        f.write("</li>\n")
        f.write("</ul>\n")
        outmod=2

      if keyword not in keyword_table:
        f.write("<p style='text-indent: 0em;'>\n")
      f.write(text+"\n")

    elif re.search(r"(^\s*(-|\.))\s\w", text): # open new item
      m=re.search(r"(^\s*(-|\.))", text)
      char=m.group()
      char=char.replace(' ','')
      text=re.sub(r"(^\s*(-|\.))\s","",text)
      if outmod==0:
        f.write("<ul>\n")
        outmod=3.1
        char_bullet=char
      elif outmod==1 or outmod==2:
        if keyword not in keyword_table:
          f.write("</p>\n")
        f.write("<ul>\n")
        outmod=3.1
        char_bullet=char
      elif outmod==3.1:
        if char_bullet=="-" and char=="-":
          f.write("</li>\n")
          outmod=3.1
        elif char_bullet=="." and char==".":
          f.write("</li>\n")
          outmod=3.1
        elif char_bullet=="-" and char==".":
          f.write("<ul>\n")
          outmod=3.2
        elif char_bullet=="." and char=="-":
          f.write("<ul>\n")
          outmod=3.2
        char_bullet=char
      elif outmod==3.2:
        if char_bullet=="-" and char=="-":
          f.write("</li>\n")
          outmod=3.2
        elif char_bullet=="." and char==".":
          f.write("</li>\n")
          outmod=3.2
        elif char_bullet=="-" and char==".":
          f.write("</li>\n")
          f.write("</ul>\n")
          f.write("</li>\n")
          outmod=3.1
        elif char_bullet=="." and char=="-":
          f.write("</li>\n")
          f.write("</ul>\n")
          f.write("</li>\n")
          outmod=3.1
        char_bullet=char

      f.write("<li>\n")
      f.write(text+"\n")

    elif re.search(r"\+--", text): # open/close a table in BIB section
      if outmod==0:
        outmod=4
        f.write("<pre>\n")
      elif outmod==1 or outmod==2:
        if keyword not in keyword_table:
          f.write("</p>\n")
        outmod=4
        f.write("<pre>\n")
        f.write(text+"\n")
      elif outmod==3.1:
        f.write("</li>\n")
        f.write("</ul>\n")
        outmod=4
        f.write("<pre>\n")
        f.write(text+"\n")
      elif outmod==3.2:
        f.write("</li>\n")
        f.write("</ul>\n")
        f.write("</li>\n")
        f.write("</ul>\n")
        outmod=4
        f.write("<pre>\n")
        f.write(text+"\n")
      elif outmod==4:
        f.write(text+"\n")
        f.write("</pre>\n")
        outmod=0

    elif re.search(r"^ \((X|Y|Z|XY|ZP)", text) and keyword=="COVARIANCE":
      if outmod==0:
        outmod=5
        f.write("<pre>\n")
        f.write(text+"\n")
      elif outmod==1 or outmod==2:
        if keyword not in keyword_table:
          f.write("</p>\n")
        outmod=5
        f.write("<pre>\n")
        f.write(text+"\n")
      elif outmod==3.1:
        f.write("</li>\n")
        f.write("</ul>\n")
        outmod=5
        f.write("<pre>\n")
        f.write(text+"\n")
      elif outmod==3.2:
        f.write("</li>\n")
        f.write("</ul>\n")
        f.write("</li>\n")
        f.write("</ul>\n")
        outmod=5
        f.write("<pre>\n")
        f.write(text+"\n")
      elif outmod==5:
        f.write(text+"\n")

    elif outmod==0: # first line of freetext
      outmod=1
      if keyword not in keyword_table:
        f.write("<p>\n")
      f.write(text+"\n")

    else:
      f.write(text+"\n")


  if outmod==1 or outmod==2:
    if keyword not in keyword_table:
      f.write("</p>\n")
  elif outmod==3.1:
    f.write("</li>\n")
    f.write("</ul>\n")
  elif outmod==3.2:
    f.write("</li>\n")
    f.write("</ul>\n")
    f.write("</li>\n")
    f.write("</ul>\n")
  elif outmod==4 or outmod==5:
    f.write("</pre>\n")

  f.write("</div>\n")


  return


def replace_free_text(text):
   text=re.sub("<","&lt;",text)
   text=re.sub(">","&gt;",text)

   urls=re.findall(r"https?://\S+", text)
   if len(urls)>0:
     for url in urls:
       link="<a href=\""+url+"\" target=\"_blank\">"+url+"</a>"
       text=re.sub(url,link,text)

   dois=re.findall(r"doi:\S+", text)
   if len(dois)>0:
     for doi in dois:
       url=re.sub("doi:","https://doi.org/",doi)
       doi1=re.sub("doi:","",doi)
       link="<a href=\""+url+"\" target=\"_blank\">"+doi1+"</a>"
       text=re.sub(doi1,link,text)

   return text


def print_table_header(f,keyword,respar):
  f.write("<thead>\n")
  f.write("<tr>\n")
  if keyword=="ANG-SEC" or keyword=="EN-SEC" or keyword=="MOM-SEC":
    headers=["Heading", "Particle considered", "Remark"]
  elif keyword=="DECAY-DATA":
    headers=["Flag", "Nuclide", "T<sub>1/2</sub>", "Type", "Energy (keV)", "Intensity", "Remark"]
  elif keyword=="DECAY-MON":
    headers=["Flag", "Nuclide", "T<sub>1/2</sub>", "Type", "Energy (keV)", "Intensity", "Remark"]
  elif keyword=="FLAG":
    headers=["Flag", "Explanation"]
  elif keyword=="ERR-ANALYS":
    headers=["Heading", "Lower limit (%)", "Upper limit (%)", "Correlation", "Remark"]
  elif keyword=="HISTORY":
    headers=["Date", "Work", "Remark"]
  elif keyword=="LEVEL-PROP":
    headers=["Flag", "Nuclide", "Heading", "Level identifier", "Level property"]
  elif keyword=="INC-SPECT" or keyword=="MISC-COL":
    headers=["Heading", "Explanation"]

  if respar:
    headers.insert(0,"Parameter #")

  for header in headers:
    f.write("<th>\n")
    f.write(header+"\n")
    f.write("</th>\n")

  f.write("</tr>\n")
  f.write("</thead>\n")

  return


def print_table(f,keyword,code,expansions,aligns,n_span_l,n_span_r,free_texts,table_out,pointer,respar):

  if not table_out:
    table_out=True
    f.write("<table>\n")
    print_table_header(f,keyword,respar)
    f.write("<tbody>\n") 

  replacements={'L': 'left', 'C': 'center', 'R': 'right'}
  aligns=[replacements.get(element,element) for element in aligns]

  f.write("<tr>\n")

  if respar:
    f.write("<td>\n")
    f.write(pointer)
    f.write("</td>\n")
  if code!="nocode":
    if n_span_l!=0:
      f.write("<td style='text-align:"+aligns[0]+"; text-wrap-mode: nowrap; border-top-style: hidden;'>\n")
    else:
      f.write("<td style='text-align:"+aligns[0]+"; text-wrap-mode: nowrap;'>\n")
    f.write("<code>\n")
    f.write(code+"\n")
    f.write("</code>\n")
    f.write("</td>\n")

  for j, expansion in enumerate(expansions):

    if j<n_span_l:
      f.write("<td style='text-align:"+aligns[j+1]+"; text-wrap-mode: nowrap; border-top-style: hidden;'>\n")
      if expansion is not None:
        f.write(expansion+"\n")
      f.write("</td>\n")
    else:
      f.write("<td style='text-align:"+aligns[j+1]+"; text-wrap-mode: nowrap;'>\n")
      if expansion is not None:
        f.write(expansion+"\n")
      f.write("</td>\n")

  if n_span_r==1: # currently only n_span_r=1 for free text field is supported
    f.write("<td style='border-top-style: hidden;'>\n")
  else:
    f.write("<td>\n")

  if unfor:
    for free_text in free_texts:
      f.write(free_text+"\n")
  else:
    print_free_text(f,keyword,free_texts)

  f.write("</td>\n")
  f.write("</tr>\n")

  return table_out


def print_date(date,mod):
  month_name = {'01' : 'January'
               ,'02' : 'February'
               ,'03' : 'March'
               ,'04' : 'April'
               ,'05' : 'May'
               ,'06' : 'June'
               ,'07' : 'July'
               ,'08' : 'August'
               ,'09' : 'September'
               ,'10' : 'October'
               ,'11' : 'November'
               ,'12' : 'December'}
  date=str(date)
  if not re.compile(r"^(19|20)").search(date):
    date="19"+date
  year=date[0:4] 
  if len(date)>4:
    month=date[4:6] 
  else:
    month=""
  if len(date)>6:
    day=date[6:8] 
  else:
    day=""

  if mod==0:
    date=year+"-"+month+"-"+day
  elif mod==1:
    date=year
  elif mod==2:
    date=year
    if month!="":
      date=month_name[month]+" "+date
    if day!="":
      date=day++" "+date
        

  return date


def print_decaydata(f,keyword,coded_information,free_texts,table_out,pointer,respar):
  if keyword=="DECAY-DATA":
    if coded_information["flag"] is not None:
      code=str(coded_information["flag"])
    else:
      code=""
  elif keyword=="DECAY-MON":
    if coded_information["heading"] is not None:
      code=coded_information["heading"]
    else:
      code=""

  nuclide=conv_nuclpart(coded_information["nuclide"],1)

  if coded_information["half-life"] is not None:
    half=str(coded_information["half-life"]["value"])
    unit=coded_information["half-life"]["unit"]
    char=dict_html_025(unit)
    if char=="?":
      unit=dict_retrieval("025","keyword",unit,"expansion")
      half_life=half+" "+unit
    else:
      half_life=half+" "+char

  else:
    half_life=""

  aligns=["R","L","R","C","R","L"]

  if coded_information["radiation"]==[]:
    expansions=[]
    expansions.append(nuclide)
    expansions.append(half_life)
    expansions.append(" ") # radiation type
    expansions.append(" ") # radiation energy
    expansions.append(" ") # radiation intensity

    table_out=print_table(f,keyword,code,expansions,aligns,0,0,free_texts,table_out,pointer,respar)

  else:
    radiations=coded_information["radiation"]
    for i, radiation in enumerate(radiations):

      expansions=[]

      if i==0:
        expansions.append(nuclide)
        expansions.append(half_life)

      else:
        expansions.append("") # nuclide
        expansions.append("") # half-life

      if radiation["radiation_type"] is not None:
        for j, radiation_type in enumerate(radiation["radiation_type"]):
          char=dict_html_033(radiation_type)
          if j==0:
            char_out=char.lower()
          else:
            char_out=char_out+"/"+char
        expansions.append(char)
      else:
        expansions.append("")

      if radiation["energy"] is not None:
        energies=[]
        for j, energy in enumerate(radiation["energy"]):
          energy=str(energy)
          if j==0:
            char=energy
          else:
            char=char+"/"+energy
        expansions.append(char)
      else:
        expansions.append("")

      if radiation["intensity"] is not None:
        intensity=str(radiation["intensity"])
        expansions.append(intensity)
      else:
        expansions.append("")


      if i==0:
        table_out=print_table(f,keyword,code,expansions,aligns,0,0,free_texts,table_out,pointer,respar)
      else:
        table_out=print_table(f,keyword,code,expansions,aligns,2,1,"",table_out,pointer,respar)

  return table_out


def print_reference(f,subentry_number,author,reference):
  if "doi" in reference:
    doi=reference["doi"]
  else:
    doi=None
  field=reference["field"]
  if author!="":
    if field["reference_type"]!="B":
      author=re.sub(r"\+"," <span style='font-style:italic'>et al.</span>",author)
      f.write(author+", ")

  if field["reference_type"]=="J":
    if doi is not None:
      f.write("<a href=\"https://doi.org/"+doi+"\">")
    title=dict_retrieval("005","code",field["reference"]["code"],"short_expansion")
    f.write(title)
    f.write(" <span style='font-weight:bold'>"+field["reference"]["volume"]+"</span>")
    if field["reference"]["issue"] is not None:
      f.write(" No."+field["reference"]["issue"])
    date=print_date(field["date"],1)
    f.write(" ("+date+")")
    f.write(" "+field["reference"]["page"])
    if doi is not None:
      f.write("</a>")

  elif field["reference_type"]=="A" or field["reference_type"]=="B" or\
       field["reference_type"]=="C":
    if field["reference_type"]=="A" or field["reference_type"]=="C":
      title=dict_retrieval("007","code",field["reference"]["code"],"long_expansion")
      if field["reference_type"]=="A":
        title="Abstract of "+title
      else:
        title="Proceedings of "+title
    else:
      title=dict_retrieval("207","code",field["reference"]["code"],"long_expansion")
    f.write(title)
    if field["reference"]["volume"] is not None:
      f.write(" Vol."+field["reference"]["volume"])
    if field["reference"]["part"] is not None:
      f.write(" Part "+field["reference"]["part"])
    if field["reference"]["page"] is not None:
      f.write(" p. "+field["reference"]["page"])
    if field["reference_type"]=="B":
      date=print_date(field["date"],1)
      f.write(" ("+date+")")

  elif field["reference_type"]=="P" or field["reference_type"]=="R" or\
       field["reference_type"]=="S" or field["reference_type"]=="X":
    f.write("Report "+field["reference"]["code"]+field["reference"]["number"])
    if field["reference"]["volume"] is not None:
      f.write("Vol."+field["reference"]["volume"])
    if field["reference"]["page"] is not None:
      f.write("p. "+field["reference"]["page"])
    institute_code=dict_retrieval("006","code",field["reference"]["code"][0:11],"institute_code")
    institute=dict_retrieval("003","code",institute_code,"expansion")
    f.write(", "+institute)
    date=print_date(field["date"],2)
    f.write(", "+date)

  elif field["reference_type"]=="T" or field["reference_type"]=="W":
    if field["reference_type"]=="T":
      f.write("Thesis by ")
    else:
      f.write("Private communication with ")
    f.write(field["reference"]["code"].capitalize())
    date=print_date(field["date"],2)
    f.write(", "+date)

  elif field["reference_type"]=="3":
      f.write(field["reference"]["code"])
      f.write(field["reference"]["version"])
      if field["reference"]["material_number"] is not None:
        f.write(", Mat number "+field["reference"]["material_number"])
      date=print_date(field["date"],1)
      f.write(" ("+date+")")


  if subentry_number!="":
    an=subentry_number[0:5]
    san=subentry_number[5:8]
    if san=="001":
      f.write(" (<a href=\"https://nds.iaea.org/EXFOR/"+an+"\" target=\"_blank\">EXFOR "+an+"</a>)\n")
    else:
      f.write(" (<a href=\"https://nds.iaea.org/EXFOR/"+an+"."+san+"\" target=\"_blank\">EXFOR "+an+"."+san+"</a>)\n")

  return


def print_reaction(f,field):
  light_particle={
                "0-G-0"  : "&gamma;+x"
               ,"0-NN-1" : "n+x"
               ,"1-H-1"  : "p+x"
               ,"1-H-2"  : "d+x"
               ,"1-H-3"  : "t+x"
               ,"2-HE-3" : "<sup>3</sup>He+x"
               ,"2-HE-4" : "&alpha;+x"}

  target=conv_nuclpart(field["target"],0)
  projectile=conv_nuclpart(field["projectile"],0)
  processes=field["process"].split("+")

  f.write(target+"(")

  if projectile=="0" and processes[0]=="F": # spontaneous fission
    f.write("sf")
  else:
    f.write(projectile+",")

    if field["process"]=="X" and field["product"] in light_particle:
        f.write(light_particle[field["product"]])
        field["product"]=""
    else:
      for process in processes:
        char=conv_nuclpart(process,0)
        f.write(char)

  f.write(")")

  if field["product"]=="ELEM":
    f.write(" charge production ")
  elif field["product"]=="MASS":
    f.write(" mass production ")
  elif field["product"]=="ELEM/MASS":
    f.write(" nuclide production ")
  elif field["product"]!="":
    product=conv_nuclpart(field["product"],0)
    f.write(product)

# particle considered (SF7)
  sfs=field["quantity_236"].split(",")
  if len(sfs)>2: # SF7 presents
    sf7=sfs[2]
    if re.search(r"\*", sf7): # wild card in SF7
      sfs=field["quantity"].split(",")
      sf7=sfs[2]
      groups=sf7.split(r"\/")
      group_chars=[]
      for group in groups:
        particles=group.split("+")
        particle_chars=[]
        for particle in particles:
          if particle=="RSD":
            expansion=conv_nuclpart(field["product"],0)
          else:
            expansion=dict_retrieval("033","code",particle,"expansion").lower()
          particle_chars.append(expansion) 
        char='+'.join(particle_chars)
        group_chars.append(char)
      particle_print='/'.join(group_chars)
      particle_print="particle considered: "+particle_print
    else:
      particle_print=""
  else:
    particle_print=""

# data type (SF9)
  data_type=field["data_type"]
  if data_type is not None:
    data_type_print="data type: "+dict_retrieval("035","code",data_type,"expansion").lower()
  else:
    data_type_print=""

  expansion=dict_retrieval("236","code",field["quantity_236"],"expansion")
  expansion=expansion.lower()
  long_expansion=dict_retrieval("236","code",field["quantity_236"],"long_expansion")
  long_expansion=long_expansion.lower()

  if long_expansion!="":
    expansion_print=long_expansion
  else:
    expansion_print=expansion

  if field["general_quantity_modifier"] is not None:
    general_quantity_modifiers=field["general_quantity_modifier"].split("/")
    for general_quantity_modifier in general_quantity_modifiers:
      expansion_print=expansion_print+", "+dict_retrieval("034","code",general_quantity_modifier,"expansion")

  if particle_print!="" and data_type_print!="":
    expansion_print+=" ("+particle_print+", "+data_type_print+")"
  elif particle_print!="" or data_type_print!="":
    expansion_print+=" ("+particle_print+data_type_print+")"
    
  f.write(" "+expansion_print+"\n")

  return


def conv_nuclpart(char,mod):
  if re.compile(r"^\d+-").search(char):
    args=char.split("-")
    symb=args[1].capitalize()
    mass=args[2]
    if mass=="0":
      mass="nat"
    if len(args)==4:
      isom=args[3].lower()
    else:
      isom=""
    char="<sup>"+mass+isom+"</sup>"+symb

  else:
    if mod==0:    # P -> p
      char=dict_html_033(char)
    elif mod==1:  # P -> protons
      char=dict_retrieval("033","code",char,"expansion")
      char=char.lower()
    
  return char


def dict_html_025(unit):
  unit_html={
   'D':   'd'
  ,'HR':  'h'
  ,'MIN': 'min'
  ,'SEC': 'sec'
  ,'YR':  'y'
  }
  if unit in unit_html:
    char=unit_html[unit]
  else:
    char="?"

  return char
  

def dict_html_033(particle):
  particle_html={
   'A':   '&alpha;'
  ,'B':   '&beta;'
  ,'B+':  '&beta<sup>+</sup>;'
  ,'B-':  '&beta<sup>-</sup>;'
  ,'DG':  '&gamma;'
  ,'G':   '&gamma;'
  ,'HE3': '<sup>3</sup>He'
  ,'TCC': 'total charge changing'
  }
  if particle in particle_html:
    char=particle_html[particle]
  else:
    char=particle.lower()

  return char
 

def dict_retrieval(dict_id,field_inp,value_inp,field_out):
  l=[x[field_out] for x in dict_json[dict_id] if x[field_inp]==value_inp]

  if len(l)==0:
    msg="code "+value_inp+" cannot be resolved by Dictionary "+dict_id
    line=""
    print_error(msg,line,force)
    value_out=value_inp
  else:
    value_out=l[0]

  return value_out


def get_file_lines(file):
  if os.path.exists(file):
    f=open(file, "r")
    lines=f.readlines()
    f.close()
  else:
    msg="File "+file+" does not exist."
    print_error_fatal(msg,"")

  return lines


def read_x4json(file_x4):
  f=open(file_x4)
  try:
    x4_json=json.load(f)
  except json.JSONDecodeError:
    msg=file_x4+" is not in JSON format."
    print_error_fatal(msg,"")

  if x4_json["title"][0:18]!="J4 - EXFOR in JSON":
    msg=file_x4+" is not an EXFOR in JSON."
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
   usage="Convert J4 file to HTML file",\
   epilog="example: x4_j4view.py -i json -d dict.json -c exfor.css -e 22742 -o exfor.html")
  parser.add_argument("-v", "--version",\
   action="version", version=ver)
  parser.add_argument("-i", "--dir_j4",\
   help="directory of input J4 files")
  parser.add_argument("-d", "--file_dict",\
   help="input JSON dictionary")
  parser.add_argument("-c", "--file_css",\
   help="input CSS file")
  parser.add_argument("-e", "--entry",\
   help="EXFOR Entry number")
  parser.add_argument("-o", "--file_html",\
   help="output HTML file")
  parser.add_argument("-l", "--limit",\
   help="number of data lines to print (optional, print all lines if negative)", default="-1")
  parser.add_argument("-f", "--force",\
   help="never prompt", action="store_true")
  parser.add_argument("-g", "--gothi",\
   help="use sans-serif (gothic) font", action="store_true")
  parser.add_argument("-u", "--unfor",\
   help="output with unformatted free text", action="store_true")

  args=parser.parse_args()
  return args


def get_input(args):
  time=datetime.datetime.now()
  date=time.strftime("%Y-%m-%d")
  print("J4VIEW (Ver."+ver+") run on "+date)
  print("-----------------------------------------")

  force0=args.force
  gothi0=args.gothi
  unfor0=args.unfor
  limit0=args.limit

  try:
    int(limit0)
  except ValueError:
    limit0=-1
  else:
    limit0=int(limit0)
  if limit0<-1:
    limit0=-1

  dir_j4=args.dir_j4
  if dir_j4 is None:
    dir_j4=input("Directory of input J4 files [j4] ---> ")
    if dir_j4=="":
      dir_j4="j4"
  if not os.path.exists(dir_j4):
    print(" ** Directory "+dir_j4+" does not exist.")
  while not os.path.exists(dir_j4):
    dir_j4=input("Directory of input J4 files [j4] ---> ")
    if dir_j4=="":
      dir_j4="j4"
    if not os.path.exists(dir_j4):
      print(" ** Directory "+dir_j4+" does not exist.")

  file_dict=args.file_dict
  if file_dict is None:
    file_dict=input("input JSON Dictionary [dict.json] --> ")
    if file_dict=="":
      file_dict="dict.json"
  if not os.path.exists(file_dict):
    print(" ** File "+file_dict+" does not exist.")
  while not os.path.exists(file_dict):
    file_dict=input("input JSON Dictionary [dict.json] --> ")
    if file_dict=="":
      file_dict="dict.json"
    if not os.path.exists(file_dict):
      print(" ** File "+file_dict+" does not exist.")

  file_css=args.file_css
  if file_css is None:
    file_css=input("input CSS file [exfor.css] ---------> ")
    if file_css=="":
      file_css="exfor.css"
  if not os.path.exists(file_css):
    print(" ** File "+file_css+" does not exist.")
  while not os.path.exists(file_css):
    file_css=input("input CSS file [exfor.css] ---------> ")
    if file_css=="":
      file_css="exfor.css"
    if not os.path.exists(file_css):
      print(" ** File "+file_css+" does not exist.")

  entry=args.entry
  if entry is None:
    entry=input("EXFOR Entry # [22742] --------------> ")
    if entry=="":
      entry="22742"
  entry_lower=entry.lower()
  pattern=dir_j4+"/"+entry_lower+".[0-9][0-9][0-9]*.json"
  all_files=glob.glob(pattern)
  files = [file for file in all_files if re.search(r"\d\d\d(\.[A-Z1-9])?", file)]
  if len(files)==0:
    print(" ** JSON file for EXFOR Entry "+entry+" does not exist.")
  while len(files)==0:
    entry=input("EXFOR Entry # [22742] --------------> ")
    if entry=="":
      entry="22742"
    entry_lower=entry.lower()
    pattern=dir_j4+"/"+entry_lower+".[0-9][0-9][0-9]*.json"
    all_files=glob.glob(pattern)
    files = [file for file in all_files if re.search(r"\d\d\d(\.[A-Z1-9])?", file)]
    if len(files)==0:
      print(" ** JSON file for EXFOR Entry "+entry+" does not exist.")

  file_html=args.file_html
  if file_html is None:
    file_html=input("output HTML file [exfor.html] ------> ")
  if file_html=="":
    file_html="exfor.html"
  if os.path.isfile(file_html):
    msg="File '"+file_html+"' exists and must be overwritten."
    print_error(msg,"",force0)

  return dir_j4,file_dict,file_css,entry,file_html,force0,gothi0,unfor0,limit0


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


def print_error_fatal(msg,line):
  print("**  "+msg)
  print(line)
  exit()


if __name__ == "__main__":
  j4view()
  exit()
