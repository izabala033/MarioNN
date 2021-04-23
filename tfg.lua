
require "pipe"

local ram = "RAM"
local nametable = "CIRAM (nametables)"



use4frames = false --lau frame ala frame bat erabili behar den


--[[
input: none
output: none

Marioren posizioak eguneratzen dira
--]]

local function getMarioPos()
	marioXw = memory.readbyte(0x0086,ram) 					--world pos 0-255
	marioxrelativew = memory.readbyte(0x03AD,ram) 			--world pos 0-255
	marioX = math.floor(marioXw / 8)						--tile pos 0-31
	marioxrelative = math.floor(marioxrelativew / 8)		--tile pos 0-31
	marioXscreen = memory.readbyte(0x006D,ram)
	lastMarioPos = marioXtotalpos			
	marioXtotalpos = marioXw+ 256*marioXscreen;
    marioyrelative = math.floor(memory.readbyte(0x00CE,ram) / 8)

	if lastMarioPos == nil then return end

	if lastMarioPos >= marioXtotalpos then
		marioStuck = marioStuck + 1
	else
		marioStuck = 0
	end


end


--[[
input: x eta y posizioak
output: CIRAM memorian (x, y) posizioan dagoen tilearen helbide fisikoa
--]]

local function getXYaddress(x, y) --0 < x < 63
	if x<32 then
		return y*32+x;
	else
		return (y*32+(x-32))+0x0400
	end

end

--[[
input: x, y posizioa; text string bat
output: none
testua irudikatzeko erabiltzen den funtzioa
--]]
local function setText( x,  y, text)
	label=forms.label(form,text,x,y,500,500)
end

--[[
input: none
output: none
Form elementu grafikoa hasieratzen da
--]]

local function startForm()
	if form == nil then
		form = forms.newform(500, 500, "map")
		setText(0,0,"");
	end

end



--[[
input: 
integer: tilearen balioa
x: tilearen x posizioa 

output: karaktere bat

grafikoki tile balioak hobeto ikusteko, formateatu egiten dira
1-1 mailan probatu da, ez daude tile guztien balioak sartuta (funtzio hau estetikoa bakarrik da, ez du ezer funtzionala egiten programaren barruan)
--]]
local function purify(integer,x)
	local textchar = 'k'
	if(integer == 36) then return '_' --background
	--coin + score numbers
	elseif (integer==0 or integer == 1 or integer == 2 or integer == 3 or integer == 4 or integer == 5 or integer == 6 or integer == 7 or integer == 8 or integer == 9) and x < 24 then return textchar
	--top letters
	elseif integer == 22 or integer == 10  or integer == 27 or integer == 18  or integer == 24  or integer == 46  or integer == 41  or integer == 32 or integer ==40 or integer ==29 or integer ==14 or integer ==21 or integer ==13  then return textchar
	--clouds
	elseif  integer == 54 or integer ==55 or integer ==57 or integer ==58 or integer ==53 or integer ==37 or integer ==56 or integer ==59 or integer ==59 or integer ==60 then return 'u'
	--mountain
	elseif  integer ==49 or integer ==50 or integer ==48 or integer ==38 or integer ==52 or integer ==51 then return 's'
	--blocks
	elseif  integer ==180 or integer ==181 or integer ==182 or integer ==183 then return 'h'
	--pipes
	elseif  integer == 96 or integer == 97 or integer == 98 or integer == 99 or integer == 100 or integer == 101 or integer == 102 or integer == 103 or integer == 104 or integer == 105 or integer == 106 then return 'P'
	--brokable brick
	elseif integer==69 or integer == 71 then return 'b'
	--? block
	elseif integer==83 or integer == 84 or integer == 85 or integer == 86 then return '?'
	--? after hit brick
	elseif integer==87 or integer == 88 or integer == 89 or integer == 90 then return 'u'
	--solid brick
	elseif integer==171 or integer == 172 or integer == 173 or integer == 174 then return 'Y' 
	--flag
	elseif integer==47 or integer == 61 or integer == 162 or integer == 163 then return 'F'
	--castle final
	elseif integer==157 or integer==158 or integer==39 or integer==169 or integer==170 or integer==156 or integer==155 then return 'c'
	else return integer
	end
end


--[[
input: none
output: none

Mario tile mapan kokatu
--]]
local function putmarioinmap()
	
	local xpos = marioxrelativew/8
	xpos = math.floor(xpos)
	
	powerup = memory.readbyte(0x0756,ram)
	if(powerup>0) then
		start=0;
	else start=2;
	end

	local char = 'o'
	for i=start,3 do

		map[xpos][marioyrelative+i]=char
		map[xpos+1][marioyrelative+i]=char 
	end
end

--[[
input:
integer: zenbatgarren etsaia den (5 daude gehienez, bakoitza RAM helbide desberdin batean)
left: pantailaren ezkerreko posizioa

output: none

etsai bat tile mapan jartzen du
--]]
local function putenemy(integer,left)
	local enemytype = memory.readbyte(integer+0x0016,ram)
	local enemyposy = math.floor(memory.readbyte(integer+0x00CF,ram)/8)
	local enemyposxtotal = memory.readbyte(integer+0x0087,ram)
	local screen = memory.readbyte(integer+0x006E)
	local totalxpos = math.floor((screen*256+enemyposxtotal)/8);
	
	if totalxpos<=left or totalxpos>=left+31 then return end --enemy offscreen


	for i=1,2 do
		map[totalxpos-left][enemyposy+i]=enemytype
		map[totalxpos-left+1][enemyposy+i]=enemytype
	end


end


--[[
input: pantailaren ezkerreko posizioa

output: none

etsai guztiak tile mapan jartzen ditu
--]]
local function 	putenemiesinmap(left)

	for i=0,4 do
		local enemyinmap = memory.readbyte(i+0x00F,ram)
		if enemyinmap == 1 then
			putenemy(i,left)
		end
	end
end

--[[
input: pantailaren ezkerreko posizioa
output: none

powerup-ak (txanpinoia, lorea, izarra, 1UP) tile mapan kokatzen ditu
--]]
local function putpowerupinmap(left)
	local isPUinmap = memory.readbyte(0x001B,ram)
	local pustate = memory.readbyte(0x0023,ram)

	if isPUinmap==0 or pustate < 6 then return --stat 0-6 -> block animation, xpos unset
	else
		
		local pustate = memory.readbyte(0x0023,ram)
		local xtotal = memory.readbyte(0x008C,ram)
		local screen = memory.readbyte(0x0073,ram)
		local xpostotal = math.floor((xtotal+screen*256)/8)
		if xpostotal<=left or xpostotal>=left+31 then return end

		local powertype = memory.readbyte(0x0039,ram)

	

		local ypos = math.floor(memory.readbyte(0x00D4,ram)/8)

		if pustate == 0xC0 or pustate == 0xC2 then ypos = ypos +1 end
		if powertype == 1 then ypos= ypos+1 end --flower y adjust
		
		if powertype == 0 then --mushroom
			char = 'm'
		elseif powertype == 1 then --flower
			char = 'f'
		elseif powertype == 2 then --star
			char = 's'
		elseif powertype == 3 then --1up
			char = 'l'
		end
		
		
		for i=1,2 do
			map[xpostotal-left][ypos+i]=char
			map[xpostotal-left+1][ypos+i]=char
		end
	end

end

--[[
input: none
output: none

q-taula hutsa hasieratu
--]]
local function createQtable()
	qtable = {}
end


--[[
input: none
output: none

tile mapa hutsa hasieratu
--]]
local function createMap()

	map = {}
	for i=0,31 do
		map[i]={}
		for j=0,29 do
			map[i][j] = ''
		end
	end
end


--[[
input: none
output: Uneko egoeraren sari metatuaren balioa
--]]
local function getScore()
	--z100 = memory.readbyte(0x07F8,ram)
	--z10 = memory.readbyte(0x07F9,ram)
	--z1 = memory.readbyte(0x07FA,ram)
	--local time = z100*100+z10*10+z1
	-- penalty = 400 - time
	local score = marioXtotalpos

	return score -- -penalty
end


--[[
input: none
output: none

tile mapa eguneratzen du pantailaratzeko
debugeatzeko informazioa ere erakusten du, adibidez puntuazio hoberena eta lortu nahi duen sari metatua

--]]

local function printMap()

	if(framecount%4 == 0) then
		stringmap = ""
		for j=0,29 do
			for i=0,31 do
				stringmap = stringmap .. " " .. map[i][j]
			end
			stringmap = stringmap .. "\n"
		end


		stringmap = stringmap .. "\n" .. " " .. "Best score: " .. bestscore .. " Target score: "..target
		stringmap = stringmap .. "\n" .. "Debug: "..debugstring
		forms.settext(label,stringmap)
	end

end


--[[
input: none
output: none

tile maparen balioak atzitzen ditu
--]]
local function updateMap()
	getMarioPos()
	local nametablepos = marioXscreen % 2
	local nametablemariopos = marioXw + 32*8*nametablepos


	leftbound = math.floor((nametablemariopos - marioxrelativew)/8)
	local rightbound = leftbound + 31;
		

	--saria, txanponak eta denborak ez du scroll egiten
	for i=0,31 do
		for j=0,3 do
			local address = getXYaddress(i,j)
			local addressvalue = memory.readbyte(address,nametable)
			map[i][j] = purify(addressvalue,i)
		end
	end


	--viewport-aren eskuin eta ezker aldea kalkulatu
	if  leftbound >= 0 and rightbound <= 63 then -- no nametable split
		for i=leftbound,leftbound+31 do
			for j=4,29 do
				local address = getXYaddress(i,j)
				local addressvalue = memory.readbyte(address,nametable)
				map[i-leftbound][j] = purify(addressvalue,i)
			end
		end
	elseif leftbound < 0 then --out of bounds from left
		left = 64+leftbound
		right = 31+leftbound 

		for i=left,63 do --left part of screen
			for j=4,29 do
				local address = getXYaddress(i,j)
				local addressvalue = memory.readbyte(address,nametable)
				map[i-left][j] = purify(addressvalue,i)
			end
		end
		for i=0,right do --right part of screen
			for j=4,29 do
				local address = getXYaddress(i,j)
				local addressvalue = memory.readbyte(address,nametable)
				map[i-leftbound][j] = purify(addressvalue,i)
			end
		end
	else --out of bounds from right
		left = leftbound
		right = rightbound%64


		for i=left,63 do --left part of screen
			for j=4,29 do
				local address = getXYaddress(i,j)
				local addressvalue = memory.readbyte(address,nametable)
				map[i-left][j] = purify(addressvalue,i)
			end
		end
		for i=0,right do --right part of screen
			for j=4,29 do
				local address = getXYaddress(i,j)
				local addressvalue = memory.readbyte(address,nametable)
				map[i+64-left][j] = purify(addressvalue,i)
			end
		end
	
	end

	--help variable to draw sprites (left screen in world coords)
	local left = math.floor((marioXw+256*marioXscreen- marioxrelativew)/8)
	
	putenemiesinmap(left)
	putpowerupinmap(left)
	putfireballsinmap()
	putmarioinmap()

	printMap() --update map
end

--[[
input: none
output: none

32x30 erabili beharrean 16x15 erabiltzeko
--]]
local function printMiniMap() --16x15 map
	stringmap = ""
	for j=0,29 do
		for i=0,31 do
			if i%2==0 and j%2==0 then
			stringmap = stringmap .. " " .. map[i][j]
			end
			
		end
		stringmap = stringmap .. "\n"
	end
	forms.settext(label,stringmap)

end


--[[
input: zein ekintza egin behar den (0, 1, 2 edo 3)
output: none

zenbaki bat emanda zein botoi edo botoi konbinazio sakatu behar diren kalkulatu
--]]
local function int2action(integer)

	action = {}
	if integer == 0 then
		action["P1 A"]="True"
		action["P1 B"]="False"
		action["P1 Right"]="False"
		lastAction = 0
	elseif integer == 1 then
		action["P1 Right"]="True"
		action["P1 A"]="False"
		action["P1 B"]="False"
		lastAction = 1
	elseif integer == 2 then
		action["P1 Right"]="True"
		action["P1 B"]="True"
		action["P1 A"]="True"
		lastAction = 2
	elseif integer == 3 then
		action["P1 Right"]="True"
		action["P1 B"]="True"
		action["P1 A"]="False"
		lastAction = 3
	elseif integer == 4 then
		action["P1 Left"]="True"
		action["P1 B"]="True"
		lastAction = 4
	elseif integer ==5 then
		action["P1 Left"]="True"
		action["P1 B"]="True"
		action["P1 A"]="True"
		lastAction = 5
	elseif integer ==6 then
		action["P1 Left"]="True"
		lastAction = 6
	end

end




--[[
input: amaierako egoera den ala ez
output: none

qtabla eguneratu
ez bada amaierako egoera, eta ez bada existitzen q-taulan, balio hori hasieratu

amaierako egoera bada, partida horretako egoera guztiak berritu, ikasitako informazioarekin

--]]

local function updateQtable(terminal)

	if not terminal then
	--update laststate/action pair using current score
		if lastState == nil or lastAction ==nil then return end

		
		stackstate[stackcount] = lastState
		stackaction[stackcount] = lastAction
		stackcount = stackcount + 1

		if qtable[lastState] == nil then
			qtable[lastState]={}
			row={}
			for i=0,3 do
				row[i]=0
			end
			qtable[lastState]= row
		
		
		end


	else
		
		--fix: aurreraka beharrean atzeraka egin, horrela batzuetan ez da beharrezkoa egoera guztiak egikaritzea
		for i = 0,stackcount-2 do

			local previndex = i 
			local nextindex = previndex + 1

			
			local maxv = -1
			for j=0,3 do
				local v = qtable[stackstate[nextindex]][j]
				if v > maxv then
					maxv = v
				end
			end
			
			finalscore = getScore()
			if maxv > finalscore then
				finalscore = maxv
			end

			qtable[stackstate[previndex]][stackaction[previndex]] = finalscore
		end 

		
		--if finalscore > bestscore then
		--	bestscore = finalscore
		--end


	end
end


--[[
input: none
output: none

mario hiltzen denean jokoa berriz hasi
--]]
local function reset()

	updateQtable(true) --terminal state,  update qtable

	deathcount = deathcount + 1
	stackcount = 0
	stackstate = {}
	stackaction = {}
	marioStuck = 0
	framecount = emu.framecount()

	if cleared then
		savestate.loadslot(2)
		savestate.saveslot(1)
	else
		savestate.loadslot(1)
	end

end


--[[
input: none
output: none

http bidez uneko egoera lortu (lau frame)
--]]
local function updateState()
	local response = getHttp("clipboard")
	state = state .. response
end


--[[
input: none
output: none

http bidez uneko egoera lortu (frame bakarra)
--]]
local function updateStateSingle()
	local response = getHttp("clipboard")
	state = response
end


--[[
input: none
output: ausazko ekintza bat

maila ur maila bada, ez da ekiprobablea izango

--]]
local function acuaticAction()
	if not acuaticlevel then
		return math.random(0,3)
	end
	local rand = math.random(0,99)
		if rand < 10 then
			rand = 0
		elseif rand < 20 then
			rand = 2
		elseif rand < 60 then
			rand = 1
		elseif rand < 100 then
			rand = 3
	end
	return rand
end



--[[
input: uneko egoera
output: none

egoera hori existitzen ez bada, qtaulan hasieratu
mario hil den ikusi, aurrerago reset egiteko

ekintza distantzia barruan badago, epsilon-greedy erabili, gehienbat ausazko ekintzak izango direnak
segurtasun distantzian badago, ekintza hoberena egin
--]]
local function getAction(statecurrent)

	updateQtable(false) --egoera ez badago qtaulan, hasieratu


	if marioStuck > mariostucktime then --mario ez bada mugitu denbora batean, reset
		syncreset = true
	end
	mariostate = memory.readbyte(0x000E,ram) --killed by enemy
	if(mariostate == 0x06 or mariostate == 0x0B) then
		syncreset = true
	end
	marioyscreen = memory.readbyte(0x00B5,ram) --zulotik behera
	if marioyscreen>1 then
		syncreset = true
	end




	if qtable[statecurrent] == nil then
		int2action(acuaticAction())
		--console.writeline("exploring first time")
	else
		maxScore = -1;
		maxAction = -1
		--maxcount = 0

		for i=0,3 do --aukeratu erabaki hoberena
			if qtable[statecurrent][i] >= maxScore then
				maxScore = qtable[statecurrent][i]
				maxAction = i
			end
		end
		target = maxScore

		local currentscore = getScore()
		local dif = maxScore - currentscore
		


		if dif > distance or cleared then --puntuazio hoberenera iristeko asko falta bada, ekintza onena aukeratu
			greed = 100
			
		elseif dif < 0 then --egoera ezezaguna
			greed = 0
		else				--puntuazio hoberena iristerakoan gauza berriak probatu
			dif = (dif * greeddiff) / distance
			greed = maxgreed - greeddiff + dif
		end


		if math.random(0,99)<greed and target > 0 then -- target > 0 bada aukeratu edozein, ez delako exploratu egoera hori,  bestela greed% ekintza hoberena
			int2action(maxAction)
			--console.writeline("exploiting...")

		else

			local rand = acuaticAction()
			int2action(rand)
			--console.writeline("exploring...")
		end

		if dif > distance and not cleared and dif - distance < 100 and lastAction == 0 then --denbora aurrezteko checkpoint bat. lastAction == 0 erabiltzen da sinkronizazio arazoak ez izateko
			savestate.saveslot(1)
		end
	end
end


--[[
input: none
output: none

maila pasa duen gorde
maila pasatzen duen bakoitzean zenbat denbora pasa den irudikatu
--]]
local function 	checkLevelCleared()
	local flag = memory.readbyte(0x001D,ram)
	if flag == 3 then
		levelcleared = true
		syncreset = true
		cleared = true
	end

	if levelcleared then
		endtime = os.time()
		elapsedtime = endtime - starttime
		console.writeline("Level cleared. Total deaths: "..deathcount..". Elapsed time: "..elapsedtime.." seconds.")
		levelcleared = false
	end

end


--[[
input: none
output: none

azken egoera zein izan den gorde
--]]
local function updateLastState()
	lastState = ""
	lastState = state
	state = ""
end




console.writeline("Starting")
savestate.loadslot(3)
savestate.saveslot(2) --backup
savestate.saveslot(1)
marioStuck = 0
state = ""
action = ""
stackcount = 0
stackstate = {}
stackaction = {}
target = 0
debugstring=""
firststate=""
bestscore = 0
deathcount = 0
levelcleared = false
starttime = os.time()
framecount = emu.framecount()
cleared = false

currentworld = memory.readbyte(0x075F,ram) + 1
currentlevel = memory.readbyte(0x0760,ram)

if currentlevel == 2 and (currentworld == 2 or currentworld == 7) then
	acuaticlevel = true
else
	acuaticlevel = false
end


syncreset = false

mariostucktime = 50


--qlearning variables
greed = 95
maxgreed = 90
greeddiff = 50
distance = 160

startForm();
createMap();
createQtable();
updateMap();
--getAction(state)

updateStateSingle()

syncaction = true
int2action(0)
joypad.set(action)


while true do
	emu.frameadvance();

	if syncreset then
		reset()
		syncreset = false
		syncaction = true
	end

	framecount = emu.framecount()
	
	if use4frames then
		updateState()
	end

	if(framecount%4 == 0) then
		if not use4frames then
			updateStateSingle()
		end
		updateMap()
		getAction(state)
		updateLastState()
		checkLevelCleared()
	end
	if syncaction then
		int2action(0)
		syncaction=false
	end
	if action ~= "" then
		joypad.set(action)
	end

end
