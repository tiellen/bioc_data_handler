#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class for handling text from bioc files for pubmed abstracts.
Writes out OG XML
Author: Tilia Ellendorff
Version: July 2015


"""
#from __future__ import division
#from __future__ import unicode_literals
from optparse import OptionParser
#import xml.etree.cElementTree as ET

import cPickle as pickle
import os

from collections import OrderedDict

from lxml import etree

from lxml.builder import E
from lxml.etree import tostring
from xml.etree.ElementTree import SubElement
import codecs

import sys  

sys.path.append('/home/user/ellendorff/additional_python/PyBioC-Jul10/src/')

from bioc import BioCReader

reload(sys)  
sys.setdefaultencoding('utf8')


# Prevent Encoding exceptions in Python 2.x
sys.stdout = codecs.getwriter('utf-8')(sys.__stdout__)
sys.stderr = codecs.getwriter('utf-8')(sys.__stderr__)
sys.stdin = codecs.getreader('utf-8')(sys.__stdin__)

    
class BioCCollectionHandler(object):
    def __init__(self, bioc_file_path, options=None, args=None):
    
        self.bioc_reader = BioCReader(bioc_file_path)
        self.bioc_reader.read()
        
        
        self.raw_collection = self.bioc_reader.collection
        self.raw_documents = self.bioc_reader.collection.documents
        
        #print self.raw_documents
        
        self.document_list = self.get_documents()
        
        self.id_list = self.get_ids()
    
        self.pmid_abstracts_dict = self.pmid_abstracts_dict()
        
        
    def get_documents(self):
        
        document_list = []
        
        for one_document in self.raw_documents:
        
            bioc_doc = BioCAbstractHandler(one_document)
        
            document_list.append(bioc_doc)

        return document_list
        
        
    def pmid_abstracts_dict(self):
        pmid_abstracts_dict = {}
        for one_doc in self.document_list:
            pmid_abstracts_dict[one_doc.id] = one_doc
        return pmid_abstracts_dict
        
    def get_document(self, pmid):
        return self.pmid_abstracts_dict[pmid]
        
    def get_ids(self):
        
        id_list = [one_doc.id for one_doc in self.document_list]
        
        return id_list
        
    def write_og_xml_files(self, output_dir):
        
        for abstract_handler in self.document_list:
            output_path = output_dir + '/' + abstract_handler.id + '_og.xml'
            #print output_path, 'output_path'
            og_writer = OG_XMLWriter(abstract_handler, output_path)
            og_writer.write()
        
        



class BioCAbstractHandler(object):
    '''Pubmed_dump_file is a file loaded as pickle file from a pubmed dump in biopython format. The functions can be used to get specific information out like abstract text, title or mesh terms out of the Pubmed_dump_file.'''

    def __init__(self, bioc_document, options=None, args=None):
    
        self.abstract_dict = self.parse_bioc_document(bioc_document)
        self.id = self.abstract_dict['pubmed_id']
        
        #self.path = dump_dir + pmid
        #self.dump_dir = dump_dir

        #print os.listdir(self.dump_dir)

        
            
    def parse_bioc_document(self, one_document):
    	'''parses a bioc document and returns an ordered dictionary with the keys 'pubmed_id', 'abstract', 'title' (keys in the dictionary are kept in original order to maintain
    	internal structure of the abstract'''
    
        abstract_dict = OrderedDict()
    
        if ':' in one_document.id:
            one_docid = one_document.id.split(':')[1]
        else: 
            one_docid = one_document.id
            
        print 'DOC ID:', one_docid
    
        abstract_dict['pubmed_id'] = one_docid


        for one_passage in one_document.passages:
            annotation_id_dict = {}
            #sentence_id = one_passage.infons['Sentence id']
            passage_name = one_passage.infons['type']
        
            passage_text = one_passage.text
            abstract_dict[passage_name] = passage_text
        
        return abstract_dict
        
    def get_abstract(self):
    	try:
        	abstract = self.abstract_dict['abstract']
        	return abstract
        except (IndexError, KeyError, TypeError):
            return ''
    
    def get_title(self):
    	try:
        	title = self.abstract_dict['title']
        	return title
        except (IndexError, KeyError, TypeError):
            return ''
    
    def get_abstract_text(self, options=None, args=None):
        try:
            abstract_text_list = []
            abstract_text_list.append(self.get_title())
            abstract_text_list.append(self.get_abstract())
            
            return ' '.join(abstract_text_list)
            
        except (IndexError, KeyError, TypeError):
            return None


    def get_whole_abstract_text(self, options=None, args=None):
        try:
            whole_abstract_list = []
            whole_abstract_list.append(self.id + '. ')
            whole_abstract_list.append(self.get_title())
            whole_abstract_list.append(self.get_abstract())

            return ' '.join(whole_abstract_list)

        except (IndexError, KeyError, TypeError):
            return None
            
    def write_og_xml(self, output_path):
        og_writer = OG_XMLWriter(self, output_path)
        og_writer.write()
        
            
class OG_XMLWriter(object):

    def __init__(self, bioc_abstract_handler, output_path, options=None, args=None):
        self.root_tree = None
                        
        self.collection = None
        self.doctype = '''<?xml version='1.0' encoding='UTF-8'?>'''
        
        self.abstract_handler = bioc_abstract_handler
        
        self.output_path = output_path
        self.pmid = bioc_abstract_handler.id
        self.article_dict = bioc_abstract_handler.abstract_dict
        
        
    def __str__(self):
        """ print writer object as string
        """
        
        self.build()
                    
        s = tostring(self.root_tree, encoding="utf-8",
                    pretty_print=True,
                    doctype=self.doctype)
                    
        return s
        
    def build(self):
    
        self._build_article()
        
    def _build_article(self):
        self.root_tree = E('article')
        self.root_tree.attrib['pid'] = self.abstract_handler.id
        self.root_tree.attrib['pmid'] = self.abstract_handler.id
        self.root_tree.attrib['pmcid'] = ''
        self.root_tree.attrib['type'] = 'Article'
        self.root_tree.attrib['year'] = ''
        self.root_tree.attrib['issn'] = ''
        
        
        for one_section in self.article_dict.keys():
            if not one_section == 'pubmed_id':
                self._build_section(one_section, self.article_dict[one_section])
                
        
    def _build_section(self, one_section, section_string):
        section_element = SubElement(self.root_tree, one_section)
        section_element.text = section_string
        
        #print one_section.lower(), 'section'
        if 'title' in one_section.lower():
            section_element.attrib['type'] = 'Title'
        elif 'abstract' in one_section.lower():
            section_element.attrib['type'] = 'Abstract'
        else: 
            section_element.attrib['type'] = ''
            print 'NO SECTION TYPE', one_section.lower()
        
    def write(self):
        #self.output_path = output_path
        if self.output_path is None:
            raise(Exception('No output file path provided.'))
        else:
            print 'write file', self.output_path
            output_file = codecs.open(self.output_path, 'w', 'utf-8')
            output_file.write(unicode(self.__str__()))
            output_file.close()
            
        
            
def process(options=None, args=None):
    """
    Do the processing.

    The options object should be used as an argument to almost all functions.
    This gives easy access to all global parameters.
    """
    #if options.debug:
    #    print >>sys.stderr, options

    #print sys.stdin, 'test'

    print 'OPTIONS:', options

    bioc_input = args[0]
    
    og_xml_out_dir = args[1]
    
    bioc_collection = BioCCollectionHandler(bioc_input)
    
    bioc_collection.write_og_xml_files(og_xml_out_dir)
    
    #parse_bioc(bioc_input)

            
def main():
    """
    Invoke this module as a script
    """
    usage = "usage: %prog [options] input: directory of pubmed dump with abstract data(args[0]); output: brat directory (args[1])"
    parser = OptionParser(version='%prog 0.99', usage=usage)

    parser.add_option('-l', '--logfile', dest='logfilename',
                      help='write log to FILE', metavar='FILE')
    parser.add_option('-q', '--quiet',
                      action='store_true', dest='quiet', default=False,
                      help='do not print status messages to stderr')
    parser.add_option('-d', '--debug',
                      action='store_true', dest='debug', default=False,
                      help='print debug information')



    (options, args) = parser.parse_args()

    if options.debug: print >> sys.stderr, '# Starting processing'

    process(options=options,args=args)




    sys.exit(0) # Everything went ok!

if __name__ == '__main__':
    main()


