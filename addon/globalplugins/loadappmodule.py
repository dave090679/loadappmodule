#coding=UTF-8
# global Plug-in for easyer loading/creating Appmodules for NVDA.
#
# erstmal das benoetigte Zeugs rankarren:-)
import wx
import gui
import globalPluginHandler
import appModuleHandler
import os
import config
import api
import ui
import subprocess
import addonHandler
addonHandler.initTranslation()
# Klasse von globalpluginhandler-globalplugin ableiten
class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	l = ''
	# unser Plugin soll an die Tastenkombination nvda+0 zugewiesen werden. Diese Zuweisung erfolgt in einem Woerterbuch, das den Namen __gestures__ haben muss.
	__gestures={
		'kb:nvda+0':'loadappmodule'
	}
	# und nun folgt das eigentliche Script. Der name des Scripts stimmt zwar nicht ganz mit dem oben angegebenen Namen ueberein (das "Script_" fehlt, das stimmt aber so:-).
	def script_loadappmodule(self, gesture):
		# die Funktion wx.CallAfter wird benutzt, um Code auszufuehren, *nachdem* alle Ereignisbehandlungsroutinen abgearbeitet sind. Dies gewaehrleistet, dass NVDA waehrend der Anzeige des meldungsfensters erwartungsgemaess reagiert. 
		# Die Funktion CallAfter erwartet als ersten Parameter den Namen der Funktion, gefolgt von allen Argumenten (wahlweise benannt oder unbenannt).
		# Wenn keine Argumente angegeben werden, wird die uebergebene Funktion (je nach Kontext) entweder ohne Argumente aufgerufen oder es wird ein Argument uebergeben, das die uebergeordnete Instanz darstellt (in unserem Fall das globale Plug-In)
		# der Kontext self ist hier notwendig, weil unsere Funktion loadappmodule (genau wie das Script auch) Bestandteil des globalplugin-Objekts ist.
		wx.CallAfter(self.loadappmodule, appModuleHandler.getAppNameFromProcessID(api.getFocusObject().processID,False))
	# Unsere Funktion loadappmodule muss ein Argument entgegennehmen, das unser globales Plug-in darstellt, weil sie Bestandteil des globalen Plug-ins ist.
	def userappmoduleexists(self, appname):
		userconfigfile = config.getUserDefaultConfigPath()+chr(92)+'appModules'+chr(92)+appname+'.py'
		if os.access(userconfigfile,os.F_OK): return userconfigfile
		else: return None

	def systemappmoduleexists(self, appname):
		sysconfigfile = config.getSystemConfigPath()+chr(92)+'appModules'+chr(92)+appname+'.py'
		if os.access(sysconfigfile,os.F_OK): return sysconfigfile
		else: return None

	def appmoduleprovidedbyaddon(self, appname):
		l = list()
		for addon in addonHandler.getRunningAddons():
			if os.access(addon.path+chr(92)+'appmodules'+chr(92)+appname+'.py',os.F_OK): l.append(addon.manifest['name'])
		if len(l) > 0: return ', '.join(l)
		else: return None

	def createnewappmodule(self, appname):
		appmodule_template = [
			'#appModules/'+appname+'.py',
			'#A part of NonVisual Desktop Access (NVDA)',
			'#Copyright (C) 2006-2012 NVDA Contributors',
			'#This file is covered by the GNU General Public License.',
			'#See the file COPYING for more details.',
			'import appModuleHandler',
			'import api',
			'class AppModule(appModuleHandler.AppModule):',
			chr(9)+'# some snapshot variables similar to these in the python console',
			chr(9)+'nav = api.getNavigatorObject()',
			chr(9)+'focus = api.getFocusObject()',
			chr(9)+'fg = api.getForegroundObject()',
			chr(9)+'rp = api.getReviewPosition()',
			chr(9)+'caret = api.getCaretObject()',
			chr(9)+'desktop = api.getDesktopObject()',
			chr(9)+'mouse = api.getMouseObject()'
		]
		if self.l != '':
			if gui.messageBox(message=self.warning_msg,
			style=wx.YES|wx.NO|wx.ICON_WARNING)==wx.NO: return
		userconfigfile = config.getUserDefaultConfigPath()+chr(92)+'appModules'+chr(92)+appname+'.py'
		fd1 = open(userconfigfile,'w')
		for line in appmodule_template:
			fd1.write(line+os.linesep)
		fd1.close()
		ui.message(_('Creating a new Appmodule for {appname}').format(appname=appname))
		self.warning_msg = ''
	def copysystouser(self, appname):
		userconfigfile = config.getUserDefaultConfigPath()+chr(92)+'appModules'+chr(92)+appName+'.py'
		sysconfigfile = config.getSystemConfigPath()+chr(92)+'appModules'+chr(92)+appName+'.py'
		fd1 = open(sysconfigfile,'r')
		fd2 = open(userconfigfile,'a')
		for line in fd1:
			fd2.write(line)
		fd2.close()
		fd1.close()

	def loadappmodule(self, appName):
		self.warning_msg = ''
		if not self.userappmoduleexists(appName):
			if  appModuleHandler.doesAppModuleExist(appName):
				self.warning_msg += _("an Appmodule for {appname} was found at the following location(s):\n").format(appname=appName)
				self.l = ''
				if self.systemappmoduleexists(appName):
					self.warning_msg += _("* in the sysconfig folder")
					self.l += 's'
				addons = self.appmoduleprovidedbyaddon(appName)
				if addons: 
					self.l += 'a'
					self.warning_msg += _("* within the following addons(s): {addons}\n").format(addons=addons)
				if self.l == '':
					self.l += 'c'
					self.warning_msg += _("There's allready an Appmodule for {appname} included in to NVDA but it is only included as a compiled file and it can't be loaded into notepad for editing.\n").format(appname=appName)
				self.warning_msg += _("If you continue and create a new appmodule, the above one(s) will stop working.\nDo you really want to create a new Appmodule?")
			self.createnewappmodule(appName)
		userconfigfile = config.getUserDefaultConfigPath()+chr(92)+'appModules'+chr(92)+appName+'.py'
		if self.warning_msg == '': subprocess.Popen(os.environ['WINDIR']+chr(92)+'notepad.exe '+chr(34)+userconfigfile+chr(34))
	script_loadappmodule.__doc__=_("Loads an Appmodule for the current Programm into notepad or creates a new one if there isn't any.")
