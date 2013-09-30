# globales Plug-in zum einfacheren erstellen/laden von Anwendungsmodulen fuer nvda.
#
# erstmal das benoetigte Zeugs rankarren:-)
import globalPluginHandler
import appModuleHandler
import os
import config
import api
import ui
import subprocess
#
# Klasse von globalpluginhandler-globalplugin ableiten
class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	# unser Plugin soll an die Tastenkombination nvda+0 zugewiesen werden. Diese Zuweisung erfolgt in einem Woerterbuch, das den Namen __gestures__ haben muss.
	__gestures={
		'kb:nvda+0':'loadappmodule'
	}
	# und nun folgt das eigentliche Script. Der name des Scripts stimmt zwar nicht ganz mit dem oben angegebenen Namen ueberein (das "Script_" fehlt, das stimmt aber so:-).
	def script_loadappmodule(self, gesture):
		# als erstes soll der name der aktuell laufenden Anwendung ermittelt werden. Dazu muss zuerst das Objekt ermittelt werden, das den Fokus hat. Eigentlich brauchen wir nicht das ganze objekt, sondern nur die ID des Prozesses, zu dem das objekt gehoert
		focus=api.getFocusObject()
		# und dann kann die Funktion getappnamefromprocessid benutzt werden, um den Namen der aktuellen Anwendng abzurufen. Diese Funktion erwartet zwei Parameter: als erstes wird die Id des Prozesses uebergeben, zu der der name abgerufen werden soll. der zweite Parameter gibt schliesslich an, ob die Dateinamenerweiterung mit zurueckgegeben werden soll. Da wir diese nicht brauchen, steht hier false.
		appName=appModuleHandler.getAppNameFromProcessID(focus.processID,False)
		# die folgende Liste enthaelt eine Vorlage fuer neueanwendungsmodule. Diese wird immer dann verwendet, wenn fuer die aktuelle Anwendung noch kein Modul existiert. Da Tab-Zeichen nicht direkt in Strin-Konstanten eingegeben werden koennen, muessen sie mit der chr-Funktion erzeugt werden. Das Tab-Zeichen besitzt den Ascii-Wert 9.
		appmodule_template = [
			'#appModules/'+appName.replace('.exe','')+'.py',
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
		# namen und vollstaendigen Pfad fuer das zu ladende Anwendungsmodul zusammensetzen:
		# - ueber die Funktionen getUserDefaultConfigPath() und getSystemConfigPath() werden die Standorte der Konfigurationsverzeichnisse abgerufen, in denen die Anwendungsmodule des aktuellen Benutzers Bzw. diejenigen fuer alle Benutzer hinterlegt sind. Auf einem deutschen Windows xp waere dies beispielsweise c:\dokumente und Einstellungen/Benutzername/Anwendungsdaten/nvda Bzw. c:\dokumente und einstellungen/all users/anwendungsdaten/nvda. 
		# - Da der inverse Schraegstrich nicht direkt als Zeichen in einer String-Konstanten eingegeben werden kann, muss er mit der Funktion chr erzeigt werden. Er besitzt den Ascii-Wert 92
		# - String-Konstanten werden durch Pluszeichen miteinander verbunden
		userconfigfile = config.getUserDefaultConfigPath()+chr(92)+'appModules'+chr(92)+appName+'.py'
		sysconfigfile = config.getSystemConfigPath()+chr(92)+'appModules'+chr(92)+appName+'.py'
		# Falls im Benutzerverzeichnis noch kein Anwendungsmodul existiert
		# - os.access Prueft die Zugriffsrechte auf eine Datei fuer den aktuellen Benutzer.
		#   - der erste Parameter gibt die zu pruefende Datei an.
		#   - der zweite parameter ist eine Konstante, die im Modul os definiert ist und angibt, welche Art des Zugriffs geprueft werden soll:
		#     - r_ok prueft, ob die Datei theoretisch zum lesen geoeffnet werden koennte.
		#     - w_ok prueft, ob die Datei theoretisch zum schreiben geoeffnet werden koennte.
		#     -  f_ok prueft, ob eine Datei existiert.
		if not os.access(userconfigfile,os.F_OK):
			# existiert jedoch eine Datei im Konfigurationsverzeichnis fuer alle Benutzer
			if os.access(sysconfigfile, os.F_OK) :
				# die systemweite Konfigurationsdatei ins Benutzerverzeichnis zeilenweise kopieren:
				# - die Funktion open oeffnet eine Datei und gibt ein Datei-objekt zurueck. der zweite Parameter gibt hierbei den Modus an, in dem die Datei geoeffnet werden soll (r = schreibgeschuetzt, a = zum Anhaengen von Daten)
				fd1 = open(sysconfigfile,'r')
				fd2 = open(userconfigfile,'a')
				# eine Datei kann - wie eine Liste oder ein Woerterbuch - in einer for-Schleife durchlaufen werden. bei jeden Durchlauf wird in der Variablen Line eine Zeile der Datei gespeichert.
				for line in fd1:
					# die Dateiobjekte besitzen die Methode write, die als parameter die zu schreibenden daten uebernimmt.
					fd2.write(line)
				# Dateien schliessen
				fd2.close()
				fd1.close()
			else:
				# Falls nirgendwo ein Anwendungsmodul existiert, wird ein neues angelegt.
				fd1 = open(userconfigfile,'w')
				for line in appmodule_template:
					# aus irgendeinem Grund versaeumt es Python, beim Schreiben von Zeilen aus unserer Vorlage diese ordentlich mit Zeilenumbruchzeichen abzuschliessen. Deshalb muss an jede Zeile die in os.linesep hinterlegte Zeichensequenz angehaengt werden.
					fd1.write(line+os.linesep)
				fd1.close()
				# eine Meldung als Blitzmeldung ausgeben (oder ansagen, wenn eine sprachausgabe aktiv ist). Die Funktion _() gehoert zu gettext und schlaegt die ihr uebergebene Meldung in der Sprachdatei fuer die aktuell eingestellte Sprache nach. Existiert keine uebersetzung, so wird die originalmeldung zurueckgegeben. 
				ui.message(_('new appmodule created.'))
		# Anwendungsmodul in den Editor laden:
		# - Das Modul subprocess besitzt die Methode Popen(), die externe programme startet, ohne auf das Ende des programms zu warten (der NVDA laeuft also im Hintergrund weiter).
		#   - als erstes wird der Editor mit vollem Pfad aufgerufen. Um das windows-Verzeichnis zu ermitteln, wird es im Woerterbuch os.environ nachgeschlagen (dieses Woerterbuch speichert die Umgebungsvariablen des Systems.
		#   - dem Editor wird der volle Pfad des Anwendungsmoduls uebergeben (in Anfuehrungszeichen eingeschlossen). Die Anfuehrungszeichen muessen hierbei mit der Funktion chr() erzeugt werden. Sie besitzen den Ascii-Wert 34.
		subprocess.Popen(os.environ['WINDIR']+chr(92)+'notepad.exe '+chr(34)+userconfigfile+chr(34))
# Dieser String speichert den hilfetext, der angezeigt und gesprochen wird, wenn ein Anwender bei eingeschalteter Eingabehilfe nvda+0 drueckt.
	script_loadappmodule.__doc__=_("tries to load the appmodule for the currently running application or creates a new file, if it dowsn't exist yet.")
