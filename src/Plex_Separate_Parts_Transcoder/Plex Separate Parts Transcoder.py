#!/usr/bin/python3

import os
import sys
import sqlite3
from sqlite3 import Error
from pathlib import Path
from datetime import datetime
from collections import OrderedDict 
import uuid
import subprocess
import signal
import ctypes

class Log:
    
    def __init__(self, jobId):
        self._jobId = jobId
        self._logFile = os.path.join(os.getenv('PLEX_LIBRARY_PATH', "/config/Library"),"Application Support", "Plex Media Server","Logs","Plex Transcoder.log")
        
        if os.path.isfile(self._logFile):
            logSize = os.path.getsize(self._logFile)
            if (logSize > 10485772):
                try:
                    logFileNameCore = self._logFile[:3]

                    for i in range (5,0,-1):
                        currentLogFile = logFileNameCore + str(i) + ".log"
                        if not os.path.isfile(currentLogFile):
                            continue
                        if i == 5:
                            os.remove(currentLogFile)
                            continue
                        os.rename(currentLogFile,logFileNameCore + str(i+1) + "log")
                    
                    os.rename(self._logFile,logFileNameCore + "1.log")
                except:
                    self.Warn("Couldn't rotate logs. Try on next run")
    
    def __getTime(self):
        return datetime.now().strftime("%b %d, %Y %H:%M:%S.%f")[:-3]

    def __writeLogRecord(self,message):
        if (os.getenv('TRANSCODER_LOGTOCONSOLE', False)):
            print (message)
        else:
            with open(self._logFile, 'a') as file:
                file.write(message + "\n")
    
    def Message(self,message,severity,jobid = None):
        if (hasattr(self, '_jobId') and (jobid is None)):
            jobid = self._jobId
        logRecord = "{0} [{1}] {2} - {3}".format(self.__getTime(),jobid, severity.upper(), str(message))
        self.__writeLogRecord(logRecord)

    def Debug(self, message, jobid = None):
        if (os.getenv('DEBUG_TRANSCODER', False)):
            self.Message(message,"DEBUG",jobid)

    def Info(self, message, jobid = None):
        self.Message(message,"INFO",jobid)
    
    def Warn(self, message, jobid = None):
        self.Message(message,"WARN",jobid)

    def Error(self, message, jobid = None):
        self.Message(message,"ERROR",jobid)


class TranscoderTransformation:

    __argumentsIterator = iter(sys.argv)
    __env = os.environ.copy()
    __conf = type('TranscoderConfiguration', (object,), dict(inputs=[], filters=[], streams=[], output=[], outputOrders=[], options=OrderedDict()))
    __sqlConn = None
    __audioMappings = dict()
    __log = Log(str(uuid.uuid4()))
    __libc = ctypes.CDLL("libc.so.6")

    EOI = "END_OF_ITER"
    PLEX_TRANSCODER = os.getenv('PLEX_PATH', "/usr/lib/plexmediaserver") + os.sep + "Plex Transcoder_org"
    PLEX_DATABASE_PATH = os.path.join(os.getenv('PLEX_LIBRARY_PATH', "/config/Library") + "Application Support","Plex Media Server","Plug-in Support","Databases","com.plexapp.plugins.library.db")

    def addAudioPartToInputs(self, audioPart):
        self.__conf.inputs.append(OrderedDict())
        self.__log.Info("Adding source '{0}' as additional input".format(audioPart.path))
        _inputPos = len(self.__conf.inputs) - 1
        if _inputPos > 0:
            if "-ss" in self.__conf.inputs[0]: self.__conf.inputs[_inputPos]["-ss"] = self.__conf.inputs[0]["-ss"]
            if "-analyzeduration" in self.__conf.inputs[0]: self.__conf.inputs[_inputPos]["-analyzeduration"] = self.__conf.inputs[0]["-analyzeduration"]
            if "-probesize" in self.__conf.inputs[0]: self.__conf.inputs[_inputPos]["-probesize"] = self.__conf.inputs[0]["-probesize"]
            if "-noaccurate_seek" in self.__conf.inputs[0]: self.__conf.inputs[_inputPos]["-noaccurate_seek"] = ""
        
        self.__conf.inputs[_inputPos]["-codec:" + str(audioPart.index)] = audioPart.codec
        self.__conf.inputs[_inputPos]["-i"] = audioPart.path
        audioPart.inputPos = _inputPos
    
    def connectDatabase(self):
        self.__log.Debug("Opening connection to SQL database")
        self.__sqlConn = sqlite3.connect(self.PLEX_DATABASE_PATH)

    def closeDatabase(self):
        if self.__sqlConn is not None:
            self.__log.Debug("Closing connection to SQL database")
            self.__sqlConn.close()

    def getArgumentsArray(self):
        self.__log.Debug("Building arguments for passing to ffmpeg")

        _args = []
        _args.append(self.PLEX_TRANSCODER)

        for _input in self.__conf.inputs:
            for _arg in _input:
                _args.append(_arg)
                _quotes = ""
                #if _arg == "-i": _quotes = '"'
                if _input[_arg] != "": _args.append(_quotes + _input[_arg] + _quotes)
        
        for _output in self.__conf.outputOrders:
            _outputDict = dict()
            if (_output.type == "stream"): _outputDict = self.__conf.streams[_output.index]
            if (_output.type == "output"): _outputDict = self.__conf.output[_output.index]
            if (_output.type == "filter"): _outputDict = {"-filter_complex": self.__conf.filters[_output.index]}
            for _arg in _outputDict:
                _args.append(_arg)
                if _outputDict[_arg] != "": _args.append(_outputDict[_arg])      
        
        for _arg in self.__conf.options:
            _args.append(_arg)
            if self.__conf.options[_arg] != "": _args.append(self.__conf.options[_arg])

        return _args
    
    def getNextArgument(self):
        ret = ""
        try:
            ret = next(self.__argumentsIterator)
        except:
            ret = self.EOI
        
        return ret

    def parseArgumets(self):
        self.getNextArgument()  # Throw away first argument, which is path to this script
        self.__log.Debug("Parsing arguments")

        argString = ""

        for arg in iter(sys.argv):
            argString += arg
            argString += " "
        self.__log.Debug(argString)

        arg = self.getNextArgument()
        curr_section = self.__conf.inputs
        while arg != self.EOI:
            #Parse inputs
            if curr_section == self.__conf.inputs:
                self.__conf.inputs.append(OrderedDict())
                curr_sec_pos = len(self.__conf.inputs) - 1
                last_arg = ""
                while last_arg != "-i" and arg != self.EOI:                        
                    if not arg in self.__conf.inputs[curr_sec_pos]:
                        self.__conf.inputs[curr_sec_pos][arg] = ""
                    if arg.startswith("-"):
                        last_arg = arg
                        value = self.getNextArgument()
                        if value.startswith("-"):
                            #actually its not a value, rather it is next argument
                            arg = value
                            continue
                        self.__conf.inputs[curr_sec_pos][arg] = value
                    arg = self.getNextArgument()

            #Parse filters
            if curr_section == self.__conf.filters:
                self.__conf.filters.append(self.getNextArgument())
                self.__conf.outputOrders.append(type('OutputPart', (object,), dict(type="filter", index=len(self.__conf.filters)-1)))
                arg = self.getNextArgument()

            #Parse streams
            if curr_section == self.__conf.streams:
                if not arg in self.__conf.streams[curr_sec_pos]:
                    self.__conf.streams[curr_sec_pos][arg] = ""
                if arg.startswith("-"):
                    self.__conf.streams[curr_sec_pos][arg] = self.getNextArgument()
                arg = self.getNextArgument()

            #Parse output
            if curr_section == self.__conf.output:
                if not arg in self.__conf.output[curr_sec_pos]:
                    self.__conf.output[curr_sec_pos][arg] = ""
                if arg.startswith("-"):
                    self.__conf.output[curr_sec_pos][arg] = self.getNextArgument()
                arg = self.getNextArgument()

            #Parse options
            if curr_section == self.__conf.options:
                if arg.startswith("-"):
                    last_arg = arg
                    if not arg in self.__conf.options:
                        self.__conf.options[arg] = ""
                else:
                    self.__conf.options[last_arg] = arg
                arg = self.getNextArgument()

            #Decide what do next
            if arg == "-filter_complex":
                curr_section = self.__conf.filters
                continue

            if arg == "-map" or arg == "-map_inlineass":
                curr_section = self.__conf.streams
                self.__conf.streams.append(OrderedDict())
                curr_sec_pos = len(self.__conf.streams) - 1
                self.__conf.outputOrders.append(type('OutputPart', (object,), dict(type="stream", index=curr_sec_pos)))
                continue

            if arg == "-f" and curr_section != self.__conf.output:
                curr_section = self.__conf.output
                self.__conf.output.append(OrderedDict())
                curr_sec_pos = len(self.__conf.output) - 1
                self.__conf.outputOrders.append(type('OutputPart', (object,), dict(type="output", index=curr_sec_pos)))
                continue

            #TODO: Find better way how to recognize options part of the commands sequence. This is depandent on the way, how current version of PMS is providing arguments.
            if arg == "-start_at_zero":
                curr_section = self.__conf.options
                continue

    def searchAudioForInput(self, inputPath, streamIndex):
        self.__log.Debug("Searching for audio input for the file {0}".format(inputPath))
        if inputPath in self.__audioMappings:
            self.__log.Debug("Audio input found in cache")
            return self.__audioMappings[inputPath]

        if self.__sqlConn is None:
            self.connectDatabase()
        _cur = self.__sqlConn.cursor()
        
        if inputPath.startswith("http://127.0.0.1:32400/library/parts/"): #if input is URL for the item, extract information about partID and ask database for the rest
            _media_part_id = inputPath.split('/')[5]
            _cur.execute('SELECT `media_item_id` FROM `media_parts` WHERE `id` = ? LIMIT 1', (_media_part_id,))
            (_media_item_id,) = _cur.fetchone()
        else: #input is path, ask database for information about this file
            _cur.execute('SELECT `id`, `media_item_id` FROM `media_parts` WHERE `file` = ? LIMIT 1', (inputPath,))
            (_media_part_id, _media_item_id) = _cur.fetchone()
        _cur.execute('SELECT `url`, `url_index`, `codec`, `language` FROM `media_streams` WHERE `media_part_id` = ? AND `media_item_id` = ? AND `index` = ? LIMIT 1', (_media_part_id, _media_item_id, streamIndex,))
        _audioPart = type('AudioPart', (object,), dict(path="", index=0, codec="", language="", inputPos = -1))
        (_urlPath, _urlIndex, _audioPart.codec, _audioPart.language) = _cur.fetchone()
        _cur.close()
        _audioPart.path = _urlPath[7:]
        _audioPart.index = streamIndex - 1000
        if _urlIndex != None:
            _audioPart.index = _urlIndex
        self.__audioMappings[inputPath] = _audioPart
        self.__log.Info("Found audio input in file {0} with index {1}".format(_audioPart.path, _audioPart.index))
        return _audioPart

    def setPdeathsig(self, sig = signal.SIGTERM):
        def callable():
            self.__log.Info("Transcoder received KILL signal")
            return self.__libc.prctl(1, sig)
        return callable

    def testIndexesForAudioPart(self, indexes):
        _inputIndex = int(indexes[0])
        _streamIndexStr = indexes[len(indexes)-1]
        if (_streamIndexStr[0] == "#"):
            _streamIndexStr = _streamIndexStr[1:]
        _streamIndex = int(_streamIndexStr, 0)
        
        if _streamIndex < 1000: 
            #lower stream index than 1000 means no alteration by separate audio agent
            return None
        
        self.__log.Info("For input '{0}', separate audio is used".format(self.__conf.inputs[_inputIndex]["-i"]))
        _audioStream = self.searchAudioForInput(self.__conf.inputs[_inputIndex]["-i"],_streamIndex)
        
        if (_audioStream.inputPos == -1):
            # Audio stream is new, inputs were not altered
            self.addAudioPartToInputs(_audioStream)
            for key in [k for k in self.__conf.inputs[_inputIndex].keys() if (":" + str(_streamIndex)) in k]:
                self.__log.Debug("Altering input {0} by removing argument '{1}'".format(_inputIndex,key))
                self.__conf.inputs[_inputIndex].pop(key,None)
        return _audioStream


    def transform(self):
        try:
            self.parseArgumets()
            
            #Extract jobId
            jobId = self.__conf.options["-progressurl"].split('/')[7]
            if (jobId is not None): self.__log = Log(jobId)
            self.__log.Info("Preparing transcoding for session {0}".format(jobId))

            
            #Check if requested media has separate audio
            for i, _filter in enumerate(self.__conf.filters):
                _indexes = _filter[_filter.find("[")+1:_filter.find("]")].split(":")
                _audioPart = self.testIndexesForAudioPart(_indexes)
                if (_audioPart) is not None:
                    _originalValue = _filter[_filter.find("["):_filter.find("]")+1]
                    self.__conf.filters[i] = _filter.replace(_originalValue,("["+ str(_audioPart.inputPos) + ":" + str(_audioPart.index) + "]"))

            for _stream in self.__conf.streams:
                if not "-map" in _stream: continue
                if (_stream["-map"].find("[") > -1): 
                    #If [ exists in map attribute, then attribute is mapping output of filter => skipping, handled in filter
                    continue 
                _indexes = _stream["-map"].split(":")
                _audioPart = self.testIndexesForAudioPart(_indexes)
                if (_audioPart) is not None:
                    _stream["-map"] = str(_audioPart.inputPos) + ":" + str(_audioPart.index)
            
            self.__conf.options["-loglevel"] = "warning"
            if (os.getenv('DEBUG_TRANSCODER', False)):
                self.__conf.options["-loglevel"] = "verbose"

            _final = self.getArgumentsArray()

            argString = ""

            for arg in _final:
                argString += arg
                argString += " "
            self.__log.Debug(argString)
            self.closeDatabase()
            
            os.environ["LD_LIBRARY_PATH_ORG"] = os.environ["LD_LIBRARY_PATH"]

            self.__log.Info("Starting transcoding for session {0}".format(jobId))

            transcoderProc = subprocess.Popen(_final, stderr=subprocess.PIPE , universal_newlines=True, preexec_fn = self.setPdeathsig(signal.SIGKILL))
            while True:
                error = transcoderProc.stderr.readline()
                if error == '' and transcoderProc.poll() is not None:
                    break
                if error:
                    self.__log.Error(error.strip())
            self.__log.Info("Transcoder ended with exit code {0}".format(transcoderProc.returncode))


            self.__log.Info("Transcoding for session {0} finished".format(jobId))
            sys.exit(transcoderProc.returncode)

        except Error as e:
            self.__log.Error(e)
            sys.exit(1)



if __name__ == '__main__':
    tt = TranscoderTransformation()
    tt.transform()
