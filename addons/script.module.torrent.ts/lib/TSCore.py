﻿#!/usr/bin/python
# -*- coding: utf-8 -*-

import httplib
import urllib
import urllib2
import re
import sys
import os
import socket
import threading
import time
import random
import json


import xbmcgui
import xbmc
import xbmcaddon

_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

Addon = xbmcaddon.Addon(id='script.module.torrent.ts')
language = Addon.getLocalizedString
addon_icon    = Addon.getAddonInfo('icon')
import TSEProgress as progress

#Надо объедениить с TSengine!!!!!!!!!
class myPlayer(xbmc.Player):
	def __init__( self, *args, **kwargs ):
		self.active = True
		self.playl=xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
		self.playl.clear()
		self.title='None'
		self.paused=None
		self.resume=None
		self.duration=None
	def playlist_add( self, url, it):
		self.playl.add(url=url, listitem= it)
		
	def play_start(self, ind=0):
		self.play(self.playl)
		self.playselected(ind)
	def onPlayBackStarted( self ):
		try: self.duration= int(xbmc.Player().getTotalTime()*1000)
		except: self.duration=0
	def onPlayBackResumed( self ):
		self.paused = False
	def onPlayBackEnded( self ):
		self.active = False
	def onPlayBackStopped( self ):
		self.active = False
	def onPlayBackPaused( self ):
		self.paused=True
	
class TSengine(object):
	
	def _TSpush(self,command):
		#print '>>'+command
		try:
			_sock.send(command+'\r\n')
		except: print 'send error'
	
	def __init__(self):
		self.addon_icon=addon_icon
		self.ready = False
		self.filelist = None
		self.files = {}
		self.file_count = None
		self.url=None
		self.player=None
		self.playing=False
		self.error_num=None
		
		#self.dialog.show()
		#self.dialog.create(language(1000), "")
		self.timeout=10
		self.mode=''
	def load_torrent(self, torrent, mode, host='127.0.0.1', port=62062 ):
		self.dialog = progress.dwprogress()
		self.dialog.updater(0,language(1001))
		self.dialog.updater(5)
		
		try:
			_sock.connect((host, port))
		except:
			self.dialog.updater(100,language(1010))
			xbmc.sleep(2000)
			#self.dialog.close()
			print "FAIL CONNECT"
			self.dialog.updater(59)
			return False
			exit
		
		self.mode=mode	
		self.r = _TSpull(1)
		self.r.start()
		comm="HELLOBG"
		self._TSpush(comm)
		self.dialog.updater(0,language(1002))
		timeout=self.timeout
		while not self.r.last_com:
			timeout=timeout-1
			if timeout==0: break
			time.sleep(1)
		if timeout==0: 
			self.dialog.updater(100,language(1011))
			xbmc.sleep(2000)
			#self.dialog.close()
			return 'No responce'
		comm='READY'
		self._TSpush(comm)
		self.ready=True
		self.dialog.updater(100,language(1003))
		self.url=torrent
		comm='LOADASYNC '+ str(random.randint(0, 0x7fffffff)) +' '+mode+' ' + torrent+ ' 0 0 0'
		self._TSpush(comm)
		timeout=self.timeout
		while not self.r.files:
			timeout=timeout-1
			if timeout==0: break
			time.sleep(1)
		if timeout==0: 
			self.dialog.updater(100,language(1012))
			xbmc.sleep(2000)
			#self.dialog.close()
			return 'Load Failed'	
		self.filelist=self.r.files
		self.file_count = self.r.count
		self.files={}
		self.dialog.updater(89)
		if self.file_count>1:
			flist=json.loads(self.filelist)
			for list in flist['files']:
				self.files[urllib.unquote_plus(urllib.quote(list[0]))]=list[1]
		elif self.file_count==1:
			flist=json.loads(self.filelist)
			list=flist['files'][0]
			self.files[urllib.unquote_plus(urllib.quote(list[0]))]=list[1]
		#print self.files
		#self.dialog.show()
		self.dialog.close()
		return 'Ok'
		

	def play_url_ind(self, index=0, title='', icon=None, thumb=None):
		self.dialog2 = progress.dwprogress()
		self.dialog2.updater(0,language(1004))
		comm='START '+self.mode+ ' ' + self.url + ' '+ str(index) +' 0 0 0'
		self._TSpush(comm)
		off_timer=180
		while not self.r.got_url:
			if self.r.last_com=='STATUS':
				try:
					if self.r.state: self.dialog2.updater(self.r.progress,self.r.state,self.r.label)
					#!!!!!!!!!тут буду использовать _com_received вместо ^^^
					pass
				except: pass
				#print "waiting"
				xbmc.sleep(1000)
				off_timer=off_timer-1
				if off_timer<=0: 
					
					break
		#print 'got url'
		self.dialog2.close()
		if self.r.got_url:
			#print self.r.got_url
			plr=myPlayer()
			lit= xbmcgui.ListItem(title, iconImage = thumb, thumbnailImage =thumb)
			self.dialog2.updater(100,language(1005))
			plr.play(self.r.got_url, lit)
			
			#self.dialog2.hide()
			#while not plr.duration:
			#	self.dialog2.updater(self.r.progress,self.r.state,self.r.label)
			#	xbmc.sleep(1000)
			#self.dialog2.hide()
			visible=False
			#print 'strat it'
			if plr.duration!=0: 
					comm='DUR '+self.r.got_url.replace('\r','').replace('\n','')+' '+str(plr.duration)
					comm='PLAYBACK '+self.r.got_url.replace('\r','').replace('\n','')+' 0'
					self._TSpush(comm)
					plr.duration=None
			while plr.active:
				#print 'active'
				
				if plr.paused: 
					#print 'paused'
					if not visible: 
						#print 'make window'
						self.dialog = progress.dwprogress()
						#self.dialog.updater(language(1000), "")
						self.dialog.updater(self.r.progress,self.r.state,self.r.label)
						visible=True
					#if visible: self.dialog2.show()
				elif visible:
					#print 'delete window'
					self.dialog.close()
					visible=False
				#print self.r.state'''
				xbmc.sleep(1000)
			#self.end()
		#else: 
		#	self.dialog.updater(0,language(1013))
		#	time.sleep(3)
		#self.dialog2.close()
		#except: pass
	def end(self):
		#print self.r.received
		try:
			comm="SHUTDOWN"
			self._TSpush(comm)
			self.r.active = False
		except: pass
		#self.r.end()
		_sock.close()
		#print 'Done'
		#try: #self.dialog.close()
		#except: pass
class _TSpull(threading.Thread):

	def _com_received(self,text):
		
		#прогресс (буфферизация, скачано)
		#сиды,пиры и скорости, если будут
		#будет self.state=[progress,state,'seeds/peers']
		try:
			#self.state=None
			#self.progress=0
			#self.label=None
			#print text
			comm=text.split(' ')[1]
			try:
				ss=re.compile('main:[a-z]+',re.S)
				s1=re.findall(ss, text)[0]
				st=s1.split(':')[1]
				#print st
				if st=='prebuf': 
					self.state=language(1100)
					self.progress=int(text.split(';')[1])+0.1
					self.label=language(1150)%(text.split(';')[8],text.split(';')[5])
				if st=='buf': 
					self.state=language(1101)
					self.progress=int(text.split(';')[1])+0.1
					self.label=language(1150)%(text.split(';')[6],text.split(';')[3])
				if st=='dl': 
					self.state=language(1102)
					self.progress=int(text.split(';')[1])+0.1
					self.label=language(1150)%(text.split(';')[6],text.split(';')[3])
				if st=='check': 
					self.state=language(1103)
					self.progress=int(text.split(';')[1])
					self.label=None
				if st=='idle': 
					self.statelanguage(1104)
					self.progress=0
				if st=='wait': 
					self.state=language(1105)
					self.label=language(1151)%(text.split(';')[1])
					self.progress=0
				#print self.state
				#print self.label
			except: pass
			#print re.search('main:prebuf;',comm)
			#print re.search('main:dl;',comm)
			return text.split(' ')[0]
		except: return text

	def __init__(self,interval):
		threading.Thread.__init__(self)
		self.daemon = True
		self.interval = interval	#Я не пользуюсь, возможно пригодится, если будет тормозить
		self.active = True			#Если пошлем False - поток остановится и перестанет принимать данные
		self.lastresolt=None		
		self.received = []			#Тут хранится все, что пришло от сервера ТС (пригодится, я думаю)
		self.last_received=None		#Последний ответ от ТССервера
		self.last_com=None			#Последняя команда от ТССервера
		self.got_url=None			#Будет ссылка на файл после буфферизации
		self.files=None				#Список файлов в json
		self.buffer=50000000			#размер буффера для приема нужен большой, если файлов много
		self.count=None
		self.state=''
		self.label=''
		self.progress=0
	def run(self):
		while self.active:
			try:
				self.last_received=_sock.recv(self.buffer)
				#print self.last_received
				#self.received.append(self.last_received)
				self.last_com = self._com_received(self.last_received)
				
				if self.last_com=='START': self.got_url=self.last_received.split(' ')[1] # если пришло PLAY URL, то забираем себе ссылку
				if self.last_com=='PLAY': self.got_url=self.last_received.split(' ')[1] # если пришло PLAY URL, то забираем себе ссылку
				if self.last_com=='LOADRESP': 
					fil = self.last_received
					ll= fil[fil.find('{'):len(fil)]
					self.files=ll
					#!!!!!!!!запихать файлы в {file:ind}
					#print self.files
					try:
						json_files=json.loads(ll)
						if json_files['status']==2:
							self.count=len(json_files['files'])
						if json_files['status']==1:
							self.count=1
						if json_files['status']==0:
							self.count=None
					except:
						self.count=None
						
			except:
				pass
		xbmc.sleep(300)
	def end(self):
		self.daemon = False


		