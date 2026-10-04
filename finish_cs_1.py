import json

PATH="cs.json"
with open(PATH,"r",encoding="utf-8") as f:
    data=json.load(f)

T={
"apps.appstore":"Obchod s aplikacemi",
"apps.cookie":"Sušenky",
"apps.voicememos":"Hlasové poznámky",
"appstore.descBlocks":"Skládej a odstraňuj řádky",
"appstore.descCookie":"Návyková klikací hra",
"appstore.descMessages":"Chatuj se svými kontakty",
"baccarat.pairRule":"Pár jsou dvě karty stejné hodnoty",
"baccarat.rebet":"Vsadit znovu",
"banking.cardColorAmber":"Jantarová",
"banking.cardColorViolet":"Fialová",
"banking.cardPatternChevron":"Krokev",
"banking.cardPatternMaze":"Bludiště",
"banking.cardPatternPinstripe":"Proužky",
"banking.debit":"Debetní",
"banking.standingCreate":"Nastavit trvalý příkaz",
"battleship.goSecond":"Hrát jako druhý",
"battleship.leaderboard":"Žebříček",
"birdy.postedPreview":"{name} zveřejnil: {preview}",
"blackjack.hit":"Táhnout",
"calendar.badEventId":"Neplatné ID události",
"calendar.goingFrom":"Účast · {name}",
"camera.filterDuotone":"Dvoutónový",
"camera.filterMono":"Černobílý",
"camera.filterSilvertone":"Stříbrný",
"camera.filterVividCool":"Živé studené",
"camera.flash":"Blesk",
"camera.hintFlash":"Blesk",
"camera.modeLandscape":"NA ŠÍŘKU",
"casino.paytable":"Výplatní tabulka",
"cherry.unmatch":"Zrušit spojení",
"cherry.unmatchName":"Zrušit spojení s {name}?",
"chess.leaderboard":"Žebříček",
"chess.stalemateDraw":"Pat, remíza",
"clock.alarm":"Budík",
"clock.badAlarmId":"Neplatné ID budíku",
"clock.hrUnit":"{h} h",
"clock.lap":"Kolo",
"clock.secUnit":"{s} s",
"clock.snooze":"Odložit",
"common.emailSubject":"E-mail {subject}",
"connectfour.leaderboard":"Žebříček",
"cookie.achA100mName":"Galaxie drobků",
"cookie.achA10kName":"Sklenice sušenek",
"cookie.achA10mName":"Říše drobků",
"cookie.achA1kDesc":"Upeč 1 000 sušenek",
"cookie.achA1mName":"Sušenkový magnát",
"cookie.achBank3Name":"Investor",
"cookie.achClk250Name":"Drtič sušenek",
"cookie.achClk50Name":"Silný klikač",
"cookie.achCps500Name":"Továrna na sušenky",
"cookie.cookieAria":"Sušenka",
"cookie.cookiesCount":"{n} sušenek",
"cookie.luckyBonus":"Štěstí! +{amount}",
"cookie.tabLeaderboard":"Žebříček",
"cookie.title":"Sušenky",
"cookie.upBankName":"Sušenková banka",
"crash.auto":"Automatický výběr",
"darkchat.unban":"Odbanovat",
"games.leaderboard":"Žebříček",
"games.youSuffix":"(ty)",
"garages.statusImpound":"Odtah",
"groups.nameYou":"{name} (ty)",
"holdem.bigBlind":"Velký blind",
"holdem.openedBy":"Otevřel {name}",
"holdem.straightFlush":"Postupka v barvě",
"homes.waypoint":"Bod na mapě",
"mail.attachMemo":"Hlasová poznámka",
"mail.bin":"Koš",
"mail.folderBin":"Koš",
"mail.folderFlagged":"Označené",
"mail.voiceMemo":"Hlasová poznámka",
"mdt.bodycam":"Tělová kamera",
"mdt.bulletinBoard":"Nástěnka",
"mdt.camerasTabBodycams":"Tělové kamery",
"mdt.cctvHintZoom":"Přibližuj kolečkem",
"mdt.courtJudge":"Soudce",
"mdt.courtVacant":"Volné",
"mdt.dashcam":"Palubní kamera",
"mdt.departmentFallback":"Terminál oddělení",
"mdt.hsMemo":"Hlasová poznámka",
"mdt.hsMemos":"Hlasové poznámky",
"mdt.hsNoteWritten":"Napsáno {when}",
"mdt.hsSketch":"Náčrt",
"mdt.iaCatNegligence":"Nedbalost",
"mdt.liveResync":"Znovu synchronizovat",
"mdt.logNounBulletins":"oznámení",
"mdt.rtStrike":"Přeškrtnutí",
"mdt.waypointShort":"Bod na mapě",
"mdt.weaponMelee":"Chladná zbraň",
"minesweeper.swept":"Vyčištěno!",
"minesweeper.wordmark":"MINY",
"music.songCount":"{count} skladba{plural}",
"notes.sketch":"Náčrt",
"notes.sketchTitle":"Náčrt",
"pages.badPostId":"Neplatné ID příspěvku",
"photos.albumNameMustCharacters":"Název alba musí mít {min}–{max} znaků"
}

def setp(path,val):
    cur=data
    parts=path.split(".")
    for p in parts[:-1]:
        cur=cur[p]
    cur[parts[-1]]=val

for k,v in T.items():
    setp(k,v)

with open(PATH,"w",encoding="utf-8") as f:
    json.dump(data,f,ensure_ascii=False,indent=2)
    f.write("\n")
print("patched",len(T))
