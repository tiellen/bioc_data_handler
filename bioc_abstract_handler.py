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

from bioc import BioCReader, BioCWriter

from bioc import BioCCollection
from bioc import BioCDocument
from bioc import BioCPassage

reload(sys)  
sys.setdefaultencoding('utf8')


# Prevent Encoding exceptions in Python 2.x
sys.stdout = codecs.getwriter('utf-8')(sys.__stdout__)
sys.stderr = codecs.getwriter('utf-8')(sys.__stderr__)
sys.stdin = codecs.getreader('utf-8')(sys.__stdin__)


class DocIDGenerator:
    '''Generates a temporal document id if input BioC document does not have id.'''
    _counter = 0
    _tid = None
    
    @classmethod
    def get(cls):
        cls._counter += 1
        cls._tid = 'temp_id' + str(cls._counter)
        
        return cls._tid
                
    

    
class BioCCollectionHandler(object):
    def __init__(self, bioc_file_path, options=None, args=None):
    
        self.bioc_reader = BioCReader(bioc_file_path)
        self.bioc_reader.read()
        
        
        self.raw_collection = self.bioc_reader.collection
        self.raw_documents = self.bioc_reader.collection.documents
        
        #print self.raw_documents
        
        self.document_list = self.get_documents(options=options, args=args)
        
        self.id_list = self.get_ids()
    
        self.pmid_abstracts_dict = self.pmid_abstracts_dict()
        
        
    def get_documents(self, options=None, args=None):
        
        document_list = []
        
        for one_document in self.raw_documents:
        
            bioc_doc = BioCAbstractHandler(one_document)
        
            document_list.append(bioc_doc)
        
        try: 
            if options.filename and len(document_list) > 1:
                if not options.pmid:
                    #print 'WARNING: more than one document in BioC file'
                    raise(Exception('More than one document in BioC file. Remove --filename option!'))
            else: pass
        except AttributeError: pass

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
        
    def write_og_xml_files(self, output_dir, options=None, args=None):
        if options.pmid:
            try:
                abstract_handler = self.pmid_abstracts_dict[options.pmid]
            except KeyError:
                raise(Exception('Target Pubmed ID could not be found in BioC collection'))
            else:
                if not options.filename:
                    output_path = output_dir + '/' + abstract_handler.id + '_og.xml'
                elif output_dir in options.filename:
                    filename = options.filename.split('/')[-1]
                    print 'FILENAME', filename
                    output_path = output_dir + '/' + filename
                    
                else:
                    'standard filename'
                    output_path = output_dir + '/' + options.filename
                    
                og_writer = OG_XMLWriter(abstract_handler, output_path)
                og_writer.write()
                
            
        else:
             
            for abstract_handler in self.pmid_abstracts_dict.values():
                
                if not options.filename:
                    output_path = output_dir + '/' + abstract_handler.id + '_og.xml'
                elif output_dir in options.filename:
                    filename = options.filename.split('/')[-1]
                    output_path = output_dir + '/' + filename
                    
                else:
                    output_path = output_dir + '/' + options.filename
                
                #print output_path, 'output_path'
                og_writer = OG_XMLWriter(abstract_handler, output_path)
                og_writer.write()
                
    def write_bioc_xml_files(self, output_dir, options=None, args=None):
        if options:
            if options.pmid:
                try:
                    abstract_handler = self.pmid_abstracts_dict[options.pmid]
                except KeyError:
                    raise(Exception('Target Pubmed ID could not be found in BioC collection'))
                else:
                    if not options.filename:
                        output_path = output_dir + '/' + abstract_handler.id + '.bioc'
                    elif output_dir in options.filename:
                        filename = options.filename.split('/')[-1]
                        print 'FILENAME', filename
                        output_path = output_dir + '/' + filename
                    
                    else:
                        output_path = output_dir + '/' + options.filename
                        
                    abstract_handler.write_text_bioc(output_path)

            elif not options.pmid:
             
                for abstract_handler in self.pmid_abstracts_dict.values():
                        if not options.filename:
                            output_path = output_dir + '/' + abstract_handler.id + '.bioc'
                        elif output_dir in options.filename:
                            if '/' in options.filename:
                                filename = options.filename.split('/')[-1]
                                output_path = output_dir + '/' + filename
                            else:
                                #output_path = os.getcwd() + '/' + filename
                                output_path = output_dir + '/' + filename
                            
                        else: output_path = output_dir + '/' + options.filename
                    
                        abstract_handler.write_text_bioc(output_path)       
               
        elif not options:
             
            for abstract_handler in self.pmid_abstracts_dict.values():
                output_path = output_dir + '/' + abstract_handler.id + '.bioc'
                abstract_handler.write_text_bioc(output_path)
                
                
        
        



class BioCAbstractHandler(object):
    '''Pubmed_dump_file is a file loaded as pickle file from a pubmed dump in biopython format. The functions can be used to get specific information out like abstract text, title or mesh terms out of the Pubmed_dump_file.'''

    def __init__(self, bioc_document, options=None, args=None):
    
        self.document = bioc_document
        self.abstract_dict = self.parse_bioc_document(bioc_document)
        self.id = self.abstract_dict['pubmed_id']
        
        #self.path = dump_dir + pmid
        #self.dump_dir = dump_dir

        #print os.listdir(self.dump_dir)

        
            
    def parse_bioc_document(self, one_document):
    	'''parses a bioc document and returns an ordered dictionary with the keys 'pubmed_id', 'abstract', 'title' (keys in the dictionary are kept in original order to maintain
    	internal structure of the abstract'''
    
        abstract_dict = OrderedDict()
        if not one_document.id == None:
            if ':' in one_document.id:
                one_docid = one_document.id.split(':')[1]
            else: 
                one_docid = one_document.id
        else: 
            one_docid = DocIDGenerator.get()
            print 'NO DOC ID FOUND; generating temporal doc id: ', one_docid
            
        #print 'DOC ID:', one_docid
    
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
            
    def write_text_bioc(self, output_path):
        bioc_writer = BioCWriter(output_path)
        bioc_collection = BioCCollection()
        # Insert option for either writing text only or annotations?
        # to keep document as it is:
        #collection.add_document(self.document)
        bioc_document = BioCDocument()
        for passage in self.abstract_dict.keys():
            bioc_passage = BioCPassage()
            bioc_passage.text = self.abstract_dict[passage]
            bioc_document.add_passage(bioc_passage)
        bioc_collection.add_document(bioc_document)
        
        print 'BioC output path', output_path
        bioc_writer.collection = bioc_collection
        bioc_writer.write()
        
          
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
    
    if options.directory:
        og_xml_out_dir = options.directory
    elif options.filename:
        if options.filename.split('/') > 1:
            og_xml_out_dir = '/'.join(options.filename.split('/')[:-1])
            #options.filenname = '/'.join(options.filename.split('/')[-1])
            
        else: 
            og_xml_out_dir = os.getcwd()
    else:
        try:
            og_xml_out_dir = args[1]
        except IndexError:
            raise(Exception('Please define output location'))
        
    if not os.path.isdir(og_xml_out_dir):
        raise(Exception('Invalid Output Directory.'))
    
    bioc_collection = BioCCollectionHandler(bioc_input, options=options, args=args)
    
    if options: 
        if not options.bioc_file:
            bioc_collection.write_og_xml_files(og_xml_out_dir, options=options)
    
        else:
            output_dir = og_xml_out_dir
            bioc_collection.write_bioc_xml_files(output_dir, options=options)
    
    #parse_bioc(bioc_input)

            
def main():
    """
    Invoke this module as a script
    """
    usage = "usage: %prog [options] input: bioc file path(args[0]); output: og xml output directory (args[1])"
    parser = OptionParser(version='%prog 0.99', usage=usage)

    parser.add_option('-l', '--logfile', dest='logfilename',
                      help='write log to FILE', metavar='FILE')
    parser.add_option('-q', '--quiet',
                      action='store_true', dest='quiet', default=False,
                      help='do not print status messages to stderr')
    parser.add_option('-d', '--debug',
                       action='store_true', dest='debug', default=False,
                       help='print debug information')
                      
    parser.add_option('-f', '--filename',
                      action='store',  type='string', dest='filename', default=False,
                      help='give a filename for output')
    parser.add_option('--directory',
                      action='store', type='string', dest='directory', default=False,
                      help='give a directory for output')
    parser.add_option('-b', '--bioc_file',
                      action='store_true', dest='bioc_file', default=False,
                      help='Generate one BioC file for each BioC Document')
                      
    parser.add_option('-p','--pmid',
                      action='store', type='string', dest='pmid', default=False,
                      help='give a single pmid for which og xml should be generated (if more than one document in bioc file)')




    (options, args) = parser.parse_args()

    if options.debug: print >> sys.stderr, '# Starting processing'

    process(options=options,args=args)




    sys.exit(0) # Everything went ok!

if __name__ == '__main__':
    main()


