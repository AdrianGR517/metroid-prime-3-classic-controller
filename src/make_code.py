"""Genera el código Gecko del mod Classic Controller para Metroid Prime 3 (RM3P01, PAL).

Salida: code.txt (texto Gecko), RM3P01.gct (binario para USB Loader GX / Dolphin), RM3P01.ini (Dolphin).
v0.6: cámara tipo FPS con el stick derecho (idea y direcciones tomadas de PrimeHack).
v0.9: controles de movimiento (agitar, látigo, palancas, cerraduras) como en PrimeHack.
"""
import struct, keystone, capstone

VERSION = "v1.0"
HOOK = 0x803c3f90   # justo después de memcpy(estado, KPADStatus, 0x84) en el sondeo del mando

# --- Botones -----------------------------------------------------------------
CL = {'UP':0x0001,'LEFT':0x0002,'ZR':0x0004,'X':0x0008,'A':0x0010,'Y':0x0020,'B':0x0040,'ZL':0x0080,
      'R':0x0200,'PLUS':0x0400,'HOME':0x0800,'MINUS':0x1000,'L':0x2000,'DOWN':0x4000,'RIGHT':0x8000}
WM = {'LEFT':0x0001,'RIGHT':0x0002,'DOWN':0x0004,'UP':0x0008,'PLUS':0x0010,'2':0x0100,'1':0x0200,
      'B':0x0400,'A':0x0800,'MINUS':0x1000,'Z':0x2000,'C':0x4000,'HOME':0x8000}
# Esquema estilo Metroid Prime Remastered (doble stick)
# v0.9b: L/R y ZL/ZR intercambiados a petición de Adrián
LOCK_BTN = 'L'          # botón de fijar blanco (el látigo se usa con él pulsado)
MAP = [('R','A'),       # disparar
       (LOCK_BTN,'Z'),  # fijar blanco
       ('ZR','DOWN'),   # misil (cruceta abajo en MP3)
       ('ZL','MINUS'),  # menú de visores
       ('B','B'),       # saltar
       ('Y','C'),       # morfosfera
       ('A','A'),       # disparar / usar
       # v0.18e: el + del clásico nunca manda el + del Wiimote (hipermodo solo con −): al pulsar = pausa (1), salvo durante una cinemática; mantener 1 s = saltar cinemática (código aparte)
       ('MINUS','PLUS'),# v0.16c: hipermodo (mantener); en el mapa pasa a ser la pista (2)
       ('HOME','HOME'),
       ('UP','2'),      # v0.16: pista del objetivo; en el mapa pasa a ser zoom + 
       ('DOWN','UP'),   # v0.17b: captura de pantalla; en el mapa es zoom -
       # v0.17b: cruceta izquierda sin uso
       ]   # v0.18: cruceta derecha sin uso (la derecha del Wiimote no hace nada conocido en MP3); libera 8 bytes
# v0.16: X ya no va a ningún botón del Wiimote: es el látigo (L + X)

# --- Ajustes -----------------------------------------------------------------
IDLE_S     = 2.0      # (modo puntero/menús) segundos con el stick derecho quieto antes de ocultar el puntero
DZ         = 0.15     # (modo puntero/menús) zona muerta del stick derecho
TB         = 60750000 # frecuencia del time base de Wii (243 MHz / 4)
YAW_RATE   = 0.060    # (modo FPS) radianes por frame con el stick a tope, horizontal (~206 grados/s a 60 fps)
PITCH_RATE = 0.040    # (modo FPS) radianes por frame con el stick a tope, vertical
AXIS_DZ    = 0.12     # (modo FPS) zona muerta por eje del stick derecho
PITCH_MAX  = 1.52     # límite de inclinación vertical (igual que PrimeHack)
# --- Mira (v0.10): centrada, pero se descentra cuando la cámara llega a un tope ----
RET_MAX_X  = 0.80     # desplazamiento máximo de la mira (unidades del juego: ±0.87 horizontal, ±0.73 vertical en PAL)
RET_MAX_Y  = 0.65
RET_SMOOTH = 0.30     # fracción del camino hacia el objetivo por frame
RET_YSIGN  = -1.0     # stick arriba -> mira arriba (cambiar a 1.0 si sale invertido)
# v0.11: la mira se descentra en los topes izquierda/derecha (cuando el juego frena el giro), no arriba/abajo.
INT_SENS   = 0.020    # pantallas de interactuar: el stick izquierdo mueve la mira (relativo, sin volver al centro)
P_ABIL = 0x35C8      # v0.12: byte de 'puede moverse' del jugador; 0 en consolas/pantallas de interactuar (hallado con volcados MEM1)
INT_FRAMES = 15       # frames con Samus quieta empujando el stick izquierdo para entrar en ese modo
MENU_SENS  = 0.020    # menús: velocidad máxima del puntero relativo (stick izquierdo)
MENU_BASE  = 0.45     # v0.11b: fracción de velocidad cerca del centro (curva: base + (1-base)*r²)
MENU_ASPECT = 16/9   # v0.11d: la pantalla es más ancha que alta; se compensa para que X e Y vayan igual en píxeles
MENU_SMOOTH = 0.35
MENU_LIM_X = 0.80     # v0.13b: límite horizontal del puntero de menús (el cursor del juego se sale de pantalla pasado ~0.87)
INT_LIM_X  = 0.50     # v0.13b: límites de la mano en consolas (estimados; antes 0.80/0.65 y se pegaba)
INT_LIM_Y  = 0.55
VISOR_SIDE_X = 0.202  # v0.15c: centros de los visores (recalibrados con 2 capturas de Adrián; coordenadas del puntero, y+ = abajo)
VISOR_SIDE_Y = 0.168
VISOR_TOP_Y  = -0.388
VISOR_DROP = 0.85     # v0.14b: menú de visores: si el stick cae más de un 15% en un frame (al soltarlo) el puntero se congela    # v0.11b: suavizado de la velocidad (quita tirones del stick de 6 bits)
# --- Controles de movimiento (v0.9, basados en PrimeHack) ---------------------
LASSO_BTN  = 'X'      # v0.16: látigo: con LOCK_BTN pulsado (fijado), X lanza el látigo y mantenerla tira
LASSO_STEP = 0.045    # avance del tirón por frame (1.0 = arrancado; ~22 frames)
ROT_RATE   = 0.040    # cerraduras de combinación / escáner ADN: velocidad con el stick izq. a tope
ROT_DZ     = 0.50     # v0.9c: todo o nada a partir de medio recorrido (como PrimeHack)
LEVER_RATE = 0.050    # palancas/manivelas: avance por frame con el stick izq. adelante/atrás
LEVER_DZ   = 0.50

# --- Direcciones RM3P01 (de PrimeHack, verificadas contra este main.dol) -------
STATE_MANAGER      = 0x805c7598  # player = *(*(SM) + 0x2184)
CURSOR_DLG_ENABLED = 0x805c96df  # byte: hay un menú con cursor abierto
LOCKON_STATE       = 0x805c76e7  # byte
CURSOR_BASE        = 0x80680240  # cursor = *(*(base) + 0xc54); +0x9c y +0x15c = posición de la mira (0 = centro)
MAP_STATE          = 0x805caa78  # v0.14: vale 3 solo con el mapa abierto (hallado con volcados)
BEAMVISOR_BASE     = 0x80680234  # *(base) + 0x1708 == 3 -> menú de visores abierto
P_XF, P_ANGMOM, P_BALL, P_LOCKTYPE, P_PITCH, P_CTRL = 0x3c, 0x174, 0x358, 0x370, 0x77c, 0x3ad8

# Parches fijos de PrimeHack (FpsControls::init_mod_mp3_standalone, PAL): quitan el giro de cámara
# por puntero del juego para que lo controlemos nosotros.
STATIC = [
    (0x80080e84, 0xec010072),  # interpolación de pitch: fmuls f0,f0,f1 -> fmuls f0,f1,f1
    (0x80152d50, 0x60000000),  # nop: el juego deja de escribir el pitch (player+0x77c)
    (0x80152d28, 0x60000000),  # nop: idem
    (0x80139860, 0x60000000),  # nop: el juego deja de escribir la velocidad de giro (player+0x174)
    (0x80138ea8, 0x60000000),  # nop: idem
    (0x80081108, 0x60000000),  # nop: pitch según el suelo
    (0x8008018c, 0x480000e4),  # beq -> b
    (0x80183dc8, 0x60000000),  # nop
    (0x8000ae44, 0x4bffaa3d),  # bl 0x80005880 (gancho de control_state, abajo)
    (0x80017258, 0x48000120),  # v0.10: salta la comprobación de límites de la mira (PrimeHack)
]
# v0.17: bola muelle (como PrimeHack, SpringballButton): en vez de preguntar al ControlMapper por el gesto
# (orden 0x32 en 0x8010CEE4), el juego lee nuestro byte. Original: addi r3,r3,0x35c4 / bl 0x800625c4.
STATIC += [(0x8010cee0, 0x3c608000),   # lis r3,0x8000
           (0x8010cee4, 0x88630000 | ((0x80005900 + 0x84) & 0xffff))]   # lbz r3,VAR+0x84(r3) (v0.18b: rA=r3; antes rA=0 leía 0x5984 y fallaba)
# v0.18d: bola impulso en X. La pulsación de la orden 0x2F se pregunta en 0x80104514 (bl 0x80160f84, que llama a
# 0x8006233c); ahí leemos nuestro byte VAR+0x85. Original: mr r4,r23 / bl 0x80160f84. Así B en morfosfera solo salta.
# (v0.18-c parcheaba por error 0x8010446C, que es un indicador de "orden activa", no la pulsación.)
STATIC += [(0x80104510, 0x3c608000),   # lis r3,0x8000
           (0x80104514, 0x88630000 | ((0x80005900 + 0x85) & 0xffff))]   # lbz r3,VAR+0x85(r3)
CTRL_HOOK_ADDR = 0x80005880
CTRL_HOOK = [0x3c60805c, 0x38637570, 0x8063002c, 0x80630004, 0x80632184,
             0x7c03f800, 0x4d820020, 0x7fe3fb78, 0x90c30078, 0x4e800020]
# Callback de extensión (0x803C624C): tratar el clásico (tipo 2) como Nunchuk (tipo 1).
EXT_PATCH = (0x803c629c, 0x4182003c)

# Variables compartidas con los parches del juego, en un hueco de ceros del DOL (0x80005900).
VAR = 0x80005900
V_SHAKE, V_TRIGGER, V_LASSO, V_HANDX, V_HANDY, V_ROT = 0x0, 0x4, 0x8, 0xc, 0x10, 0x14
V_CLHOLD, V_SKIPT, V_SKIPON = 0x1c, 0x20, 0x24
V_SPRING = 0x84    # v0.18: byte = B del clásico pulsada (bola muelle); +0x85 = X (bola impulso)
V_PCNT = 0x80      # v0.16f: frames con el + del clásico pulsado (sin uso desde v0.18f)
V_HBMT = 0x8c      # v1.0: time base de la última vez que corrió el menú HOME de la Wii
HBM_T = int(0.2 * 60750000)   # v1.0: menú HOME abierto hace menos de 0,2 s: el mod no toca el mando
V_CUTT = 0x88      # v0.18g: time base de la última vez que corrió el código de cinemáticas
CUT_T = int(0.2 * 60750000)   # v0.18g: si corrió hace menos de 0,2 s, hay cinemática: + no pausa
PAUSE_TAP = 24     # v0.16f: + pulsado menos de 24 frames (~0,4 s) = pausa al soltar   # botones del clásico pulsados; temporizador de saltar cinemática
MOTION_VF = 0x802e3be4    # función de la vtable de los puzles de movimiento (palancas)

def A1(src, addr=0):
    e, _ = ks.asm(src, addr); return [int.from_bytes(bytes(e[i:i+4]), 'big') for i in range(0, len(e), 4)]
ks = keystone.Ks(keystone.KS_ARCH_PPC, keystone.KS_MODE_PPC32 | keystone.KS_MODE_BIG_ENDIAN)
def lis_ori(r, a): return A1(f"lis {r},0x{a>>16:x}; ori {r},{r},0x{a&0xffff:x}")

# Parches de movimiento de PrimeHack (MP3 standalone PAL), con direcciones verificadas en este main.dol.
LASSO_F1, LASSO_F2, LASSO_F3 = 0x800dfc4c, 0x80175914, 0x801766fc
lx, ly, ls_ = lis_ori(11, VAR+V_HANDX), lis_ori(11, VAR+V_HANDY), lis_ori(30, VAR+V_LASSO)
lt, lr = lis_ori(3, VAR+V_TRIGGER), lis_ori(12, VAR+V_ROT)
MOTION = [
    # ProcessGrappleLasso: tensión/amarillo según hand_x, y su valor de retorno según nuestra variable
    (LASSO_F1+0x0, lx[0]), (LASSO_F1+0x4, lx[1]), (LASSO_F1+0xc, 0xc04b0000),
    (LASSO_F1+0x8, 0x40800158), (LASSO_F1+0x18, 0x40810148), (LASSO_F1+0x54, 0x4800010c),
    (LASSO_F1+0x160, ls_[0]), (LASSO_F1+0x164, ls_[1]), (LASSO_F1+0x168, 0x83de0000),
    # animación del brazo tirando
    (LASSO_F2+0x0, lx[0]), (LASSO_F2+0x4, lx[1]), (LASSO_F2+0x8, 0xc00b0000),
    (LASSO_F2+0xc, ly[0]), (LASSO_F2+0x10, ly[1]), (LASSO_F2+0x14, 0xc04b0000), (LASSO_F2+0x18, 0xd05701c8),
    # "¿se ha lanzado el látigo?" -> devuelve nuestra variable
    (LASSO_F3+0x0, lt[0]), (LASSO_F3+0x4, lt[1]), (LASSO_F3+0x8, 0x80630000), (LASSO_F3+0xc, 0x4e800020),
    # cerraduras de combinación y escáner ADN: velocidad de giro desde nuestra variable
    (0x801fc5a8, lr[0]), (0x801fc5b0, lr[1]), (0x801fc5b8, 0xc02c0000),
    (0x801fe7c8, lr[0]), (0x801fe7cc, lr[1]), (0x801fe7d0, 0xc02c0000),
]
# deslizamiento por el látigo (add_grapple_slide_code_mp3)
_sl = A1("nop; nop; nop; lfs 0,0x240(1); stfs 0,0x48(31); lfs 0,0x244(1); stfs 0,0x58(31); lfs 0,0x248(1); stfs 0,0x68(31)")
MOTION += [(0x801837dc + 4*i, w) for i, w in enumerate(_sl)] + [(0x801837dc + 0x28, A1("addi 4,31,0x3c")[0])]
# Agitar el mando (0x800A938C, original li r26,0): r26 = nuestra variable (B pulsado)
SHAKE_HOOK = 0x800a938c
SHAKE_ASM = A1(f"lis 26,0x{VAR>>16:x}; lwz 26,0x{VAR&0xffff:x}(26)")

def f2u(v): return struct.unpack('>I', struct.pack('>f', v))[0]
def hi(a): return ((a + 0x8000) >> 16) & 0xffff
def lo(a):
    l = a & 0xffff
    return l - 0x10000 if l >= 0x8000 else l

assert RET_YSIGN == -1.0  # v0.16d: la constante SY se reutiliza como signo de la mira
NSLOT = len(MAP)  # v0.16g: solo los huecos usados (antes 15)
NSLOT_OLD = 15                      # huecos fijos en la tabla, para que el configurador pueda cambiarla sin reensamblar
# v0.18: los botones del clásico que van al mismo botón del Wiimote comparten entrada (máscara combinada):
# R+A -> A y +/- -> +. Ahorra 16 bytes. El bucle ya hace "si algún bit de la máscara está pulsado".
_grp = {}
for c, w in MAP:
    _grp[w] = _grp.get(w, 0) | CL[c]
TABLE = [(m, WM[w]) for w, m in _grp.items()]
NSLOT = len(TABLE)
N = NSLOT
SHAKE_BTN = 'B'
K = [('SY',-1.0),('ONE',1.0),('ZERO',0.0),('DZ2',DZ*DZ),('YAW',YAW_RATE),('PITCH',PITCH_RATE),
     ('PMAX',PITCH_MAX),('PMIN',-PITCH_MAX),('HALF',0.5),('SIXTH',1/6),('INV24',1/24),('TINY',1e-7),('ADZ',AXIS_DZ),
     ('LSTEP',LASSO_STEP),('QUARTER',0.25),('ROT',ROT_RATE),('ROTDZ',ROT_DZ),('LEVER',LEVER_RATE),('LDZ',LEVER_DZ),
     ('RMX',RET_MAX_X),('RMY',RET_MAX_Y),('RSM',RET_SMOOTH),
     ('LSENS',INT_SENS),('MSENS',MENU_SENS),('MBASE',MENU_BASE),('MCUR',1-MENU_BASE),('MSM',MENU_SMOOTH),('MSX',MENU_ASPECT**-0.5),('MSY',-(MENU_ASPECT**0.5)),('MLX',MENU_LIM_X),('IMX',INT_LIM_X),('IMY',INT_LIM_Y),('VDROP',VISOR_DROP),('VSX',VISOR_SIDE_X),('VSY',VISOR_SIDE_Y),('VTY',VISOR_TOP_Y)]
KO = {name: 4*i for i,(name,_) in enumerate(K)}
# v0.16d: las variables viven en el hueco de ceros del DOL (VAR+0x40.., base r8) y no dentro del código
MLOCK_OFF = 4*len(K); MLASSO_OFF = MLOCK_OFF + 4; MSHAKE_OFF = MLASSO_OFF + 4   # máscaras de botones (editables por el configurador)
VB = 0x40
LAST_OFF = VB; ACCF_OFF = VB + 4; ACC_OFF = VB + 8                 # v0.9c: acelerómetro del Wiimote congelado
RX_OFF = VB + 20; RY_OFF = VB + 24                                 # v0.10: desplazamiento actual de la mira
PX_OFF = VB + 28; PY_OFF = VB + 32; POS_OFF = VB + 36              # v0.11 / v0.14b (POS y POS+4)
IMODE_OFF = VB + 44; W_OFF = VB + 48                               # W y W+4
VX_OFF = VB + 56; VY_OFF = VB + 60                                 # v0.11b: velocidad suavizada del puntero de menús

def valid_ptr(reg, fail):
    # salta a `fail` si reg no está en 0x80000000..0x817FFFFF
    return f"""  addis 12,{reg},-0x8000
  lis 11,0x0180
  cmplw 12,11
  bge {fail}
"""

def neg_ptr(reg, fail):
    # v0.16g: comprobación corta: salta a `fail` si reg no es negativo (null = 0); 2 instrucciones en vez de 4
    return f"""  cmpwi {reg},0
  bge {fail}
"""

asm = f"""
  lis 4,0x{VAR>>16:x}
  lwz 4,{(VAR&0xffff)+V_HBMT}(4)
  mftb 3
  subf 3,4,3
  lis 4,0x{HBM_T>>16:x}
  ori 4,4,0x{HBM_T&0xffff:x}
  cmplw 3,4
  blt end
  lbz 3,0x5c(29)
  cmpwi 3,2
  beq isclassic
  lwz 4,0x0(29)
  lis 3,0x{VAR>>16:x}
  rlwinm 0,4,22,31,31
  stb 0,{(VAR&0xffff)+V_SPRING+1}(3)
  rlwinm 4,4,6,21,21
  stw 4,{(VAR&0xffff)+0x1C}(3)
  b end
isclassic:
  bl data_end
""" + ''.join(f"  .long 0x{e[0]:08x}\n  .long 0x{e[1]:08x}\n" for e in TABLE) \
    + ''.join(f"  .long 0x{f2u(v):08x}\n" for _,v in K) \
    + f"  .long 0x{CL[LOCK_BTN]:08x}\n  .long 0x{CL[LASSO_BTN]:08x}\n  .long 0x{CL[SHAKE_BTN]:08x}\n" + f"""
data_end:
  mflr 8
  lwz 4,0x60(29)
  lwz 5,0x64(29)
  lwz 6,0x68(29)
  lwz 9,0x0(29)
  lwz 10,0x4(29)
  lwz 11,0x8(29)
  lwz 0,{N*8+MLOCK_OFF}(8)
  and. 0,4,0
  beq noclr
  lwz 0,{N*8+MLASSO_OFF}(8)
  andc 4,4,0
  andc 5,5,0
noclr:
  li 12,{N}
  mtctr 12
  addi 7,8,-8
loop:
  lwzu 12,8(7)
  lwz 3,4(7)
  and. 0,4,12
  beq s1
  or 9,9,3
s1:
  and. 0,5,12
  beq s2
  or 10,10,3
s2:
  and. 0,6,12
  beq s3
  or 11,11,3
s3:
  bdnz loop
  # v0.18g: classic + sends WM 1 (pause) as soon as it is pressed, unless a cutscene is running:
  # the cutscene-skip code stamps the time base in V_CUTT every frame it runs (only during cutscenes)
  andi. 0,5,0x{CL['PLUS']:x}
  beq pnop
  lis 12,0x8000
  mftb 3
  lwz 0,{(VAR&0xffff)+V_CUTT}(12)
  subf 3,0,3
  lis 0,0x{CUT_T>>16:x}
  ori 0,0,0x{CUT_T&0xffff:x}
  cmplw 3,0
  blt pnop
  ori 9,9,0x{WM['1']:x}
  ori 10,10,0x{WM['1']:x}
pnop:
  stw 9,0x0(29)
  stw 10,0x4(29)
  stw 11,0x8(29)
  lfs 1,0x6c(29)
  lfs 2,0x70(29)
  lfs 3,0x74(29)
  lfs 4,0x78(29)
  addi 7,8,{N*8}
  lfs 7,{KO['ONE']}(7)
  lfs 8,{KO['ZERO']}(7)
  lis 8,0x{VAR>>16:x}
  ori 8,8,0x{VAR&0xffff:x}
  lwz 4,0x60(29)
  stw 4,{V_CLHOLD}(8)
  rlwinm 3,4,26,31,31
  stb 3,{V_SPRING}(8)
  rlwinm 3,4,29,31,31
  stb 3,{V_SPRING+1}(8)
  lwz 0,{MSHAKE_OFF}(7)
  and. 3,4,0
  li 3,0
  beq noshake
  li 3,1
noshake:
  stw 3,{V_SHAKE}(8)
  lwz 0,{MLOCK_OFF}(7)
  lwz 3,{MLASSO_OFF}(7)
  or 0,0,3
  and 3,4,0
  cmpw 3,0
  li 3,0
  bne notrig
  li 3,1
notrig:
  stw 3,{V_TRIGGER}(8)
  lfs 13,{KO['ROTDZ']}(7)
  fabs 5,1
  fsubs 5,5,13
  lfs 13,{KO['ROT']}(7)
  fneg 6,13
  fsel 6,1,13,6
  fsel 6,5,6,8
  stfs 6,{V_ROT}(8)
  stfs 1,0x60(29)
  stfs 2,0x64(29)
  stfs 8,0x68(29)
  stfs 8,0x6c(29)
  stfs 8,0x70(29)
  stfs 8,0x74(29)
  stfs 8,0x78(29)
  stfs 8,0x28(29)
  stfs 8,0x2c(29)
  stfs 8,0x30(29)
  stfs 7,0x34(29)
  stfs 8,0x38(29)
  stfs 7,0x48(29)
  li 3,1
  stb 3,0x5c(29)

  lwz 3,{ACCF_OFF}(8)
  cmpwi 3,0
  bne acc_have
  lfs 5,0x18(29)
  lfs 6,{KO['HALF']}(7)
  fcmpu 0,5,6
  blt acc_skip
  lwz 3,0xc(29)
  stw 3,{ACC_OFF}(8)
  lwz 3,0x10(29)
  stw 3,{ACC_OFF+4}(8)
  lwz 3,0x14(29)
  stw 3,{ACC_OFF+8}(8)
  li 3,1
  stw 3,{ACCF_OFF}(8)
acc_have:
  lwz 3,{ACC_OFF}(8)
  stw 3,0xc(29)
  lwz 3,{ACC_OFF+4}(8)
  stw 3,0x10(29)
  lwz 3,{ACC_OFF+8}(8)
  stw 3,0x14(29)
  stfs 7,0x18(29)
  stfs 8,0x1c(29)
acc_skip:

  lis 9,{hi(CURSOR_DLG_ENABLED)}
  lbz 10,{lo(CURSOR_DLG_ENABLED)}(9)
  cmpwi 10,0
  bne ptrmode
  lis 9,{hi(STATE_MANAGER)}
  lwz 9,{lo(STATE_MANAGER)}(9)
{neg_ptr(9,'ptrmode')}  lwz 9,0x2184(9)
{neg_ptr(9,'ptrmode')}  lis 10,{hi(BEAMVISOR_BASE)}
  lwz 10,{lo(BEAMVISOR_BASE)}(10)
{neg_ptr(10,'novisor')}  lwz 10,0x1708(10)
  cmpwi 10,3
  beq visormode
novisor:
  lwz 10,{P_LOCKTYPE}(9)
  lfs 9,{V_HANDX}(8)
  cmpwi 10,2
  bne lasso_off
  lwz 3,{V_TRIGGER}(8)
  lfs 13,{KO['LSTEP']}(7)
  cmpwi 3,0
  bne lasso_up
  fneg 13,13
lasso_up:
  fadds 9,9,13
  fsel 9,9,9,8
  fsubs 5,7,9
  fsel 9,5,9,7
  li 3,2
  fcmpu 0,9,7
  blt lasso_store
  li 3,4
  b lasso_store
lasso_off:
  fmr 9,8
  li 3,0
lasso_store:
  stw 3,{V_LASSO}(8)
  stfs 9,{V_HANDX}(8)
  lfs 13,{KO['QUARTER']}(7)
  fmuls 5,9,13
  stfs 5,{V_HANDY}(8)

  fabs 5,1
  fabs 6,2
  fadds 5,5,6
  lfs 13,{KO['LDZ']}(7)
  fcmpu 0,5,13
  blt lever_done
  lis 3,{hi(STATE_MANAGER)}
  lwz 3,{lo(STATE_MANAGER)}(3)
{neg_ptr(3,'lever_done')}  lwz 3,0x1010(3)
{neg_ptr(3,'lever_done')}  addi 4,3,4
  li 0,2048
  mtctr 0
lever_loop:
  lwz 6,0(4)
{valid_ptr(6,'lever_next')}  lwz 10,0x38(6)
  andis. 0,10,0x0010
  bne lever_proc
  andis. 0,10,0x2000
  beq lever_next
  andis. 0,10,0x0020
  bne lever_next
lever_proc:
  lwz 5,0(6)
{valid_ptr(5,'lever_next')}  lwz 5,0xc(5)
  lis 12,{hi(MOTION_VF)}
  addi 12,12,{lo(MOTION_VF)}
  cmplw 5,12
  bne lever_next
  lwz 5,0x14c(6)
  cmpwi 5,3
  bne lever_next
  lwz 5,0xd0(6)
  cmpwi 5,2
  lfs 10,0x1e8(6)
  fneg 12,10
  fneg 11,2
  fsel 11,12,2,11
  bne lv_apply
  lfs 10,0x210(6)
  fneg 11,1
  fsel 11,10,11,1
lv_apply:
  lfs 13,{KO['LDZ']}(7)
  fabs 5,11
  fsubs 5,5,13
  lfs 13,{KO['LEVER']}(7)
  fneg 6,13
  fsel 6,11,13,6
  fsel 6,5,6,8
  lfs 9,0x154(6)
  fadds 9,9,6
  fsel 9,9,9,8
  fsubs 5,7,9
  fsel 9,5,9,7
  stfs 9,0x154(6)
lever_next:
  lhz 5,6(4)
  cmplwi 5,0xffff
  beq lever_done
  slwi 5,5,3
  add 4,3,5
  addi 4,4,4
  bdnz lever_loop
lever_done:
  lwz 10,{P_LOCKTYPE}(9)
  cmpwi 10,1
  beq fpsnocam
  cmpwi 10,0
  bne nolock
  lis 11,{hi(LOCKON_STATE)}
  lbz 11,{lo(LOCKON_STATE)}(11)
  cmpwi 11,0
  bne fpsnocam
nolock:
  lwz 10,{P_BALL}(9)
  cmpwi 10,0
  bne fpsnocam
  lwz 10,{P_CTRL}(9)
{neg_ptr(10,'fpsnocam')}  lwz 10,0x7cc(10)
  cmpwi 10,1
  bne fixedcam

  lfs 13,{KO['ADZ']}(7)
  fabs 5,3
  fsubs 5,5,13
  fsel 3,5,3,8
  fabs 5,4
  fsubs 5,5,13
  fsel 4,5,4,8
  lbz 3,{P_ABIL}(9)
  cntlzw 3,3
  srwi 3,3,5
  stw 3,{IMODE_OFF}(8)
idone:
  lwz 3,{IMODE_OFF}(8)
  cmpwi 3,0
  beq notint
  lfs 13,{KO['LSENS']}(7)
  lfs 10,{RX_OFF}(8)
  fmadds 10,1,13,10
  lfs 13,{KO['IMX']}(7)
  fsubs 11,13,10
  fsel 10,11,10,13
  fneg 11,13
  fsubs 12,10,11
  fsel 10,12,10,11
  stfs 10,{RX_OFF}(8)
  lfs 13,{KO['LSENS']}(7)
  lfs 10,{RY_OFF}(8)
  fmadds 10,2,13,10
  lfs 13,{KO['IMY']}(7)
  fsubs 11,13,10
  fsel 10,11,10,13
  fneg 11,13
  fsubs 12,10,11
  fsel 10,12,10,11
  stfs 10,{RY_OFF}(8)
  b rdone
notint:
  # v0.18h: sin desplazamiento de la mira hacia los bordes al girar: siempre centrada en modo FPS
  stfs 8,{RX_OFF}(8)
  stfs 8,{RY_OFF}(8)
rdone:
  fabs 5,3
  fmuls 5,5,3
  lfs 13,{KO['YAW']}(7)
  fmuls 5,5,13
  fneg 5,5
  fabs 6,4
  fmuls 6,6,4
  lfs 13,{KO['PITCH']}(7)
  fmuls 6,6,13
  lfs 9,{P_PITCH}(9)
  fadds 9,9,6
  lfs 13,{KO['PMAX']}(7)
  fsubs 10,13,9
  fsel 9,10,9,13
  lfs 13,{KO['PMIN']}(7)
  fsubs 10,9,13
  fsel 9,10,9,13
  stfs 9,{P_PITCH}(9)
  fmuls 10,5,5
  lfs 13,{KO['SIXTH']}(7)
  fmuls 11,10,13
  fmuls 11,11,5
  fsubs 11,5,11
  lfs 13,{KO['HALF']}(7)
  fmuls 12,10,13
  fsubs 12,7,12
  fmuls 10,10,10
  lfs 13,{KO['INV24']}(7)
  fmuls 10,10,13
  fadds 12,12,10
""" + ''.join(f"""  lfs 1,{P_XF+4*j}(9)
  lfs 2,{P_XF+16+4*j}(9)
  fmuls 5,12,1
  fnmsubs 5,11,2,5
  fmuls 6,11,1
  fmadds 6,12,2,6
  stfs 5,{P_XF+4*j}(9)
  stfs 6,{P_XF+16+4*j}(9)
""" for j in range(3)) + f"""  lfs 13,{KO['TINY']}(7)
  stfs 13,{P_ANGMOM}(9)
  b writecur

fixedcam:
  lfs 13,{KO['ADZ']}(7)
  fabs 5,3
  fsubs 5,5,13
  fsel 3,5,3,8
  fabs 5,4
  fsubs 5,5,13
  fsel 4,5,4,8
  lfs 13,{KO['ADZ']}(7)
  fabs 5,1
  fsubs 5,5,13
  fsel 5,5,1,8
  fadds 3,3,5
  fabs 5,2
  fsubs 5,5,13
  fsel 5,5,2,8
  fadds 4,4,5
  fneg 6,7
  fsubs 5,7,3
  fsel 3,5,3,7
  fsubs 5,3,6
  fsel 3,5,3,6
  fsubs 5,7,4
  fsel 4,5,4,7
  fsubs 5,4,6
  fsel 4,5,4,6
  lfs 12,{KO['RSM']}(7)
  lfs 13,{KO['RMX']}(7)
  fmuls 11,3,13
  lfs 10,{RX_OFF}(8)
  fsubs 11,11,10
  fmadds 10,11,12,10
  stfs 10,{RX_OFF}(8)
  lfs 13,{KO['RMY']}(7)
  fmuls 11,4,13
  lfs 10,{RY_OFF}(8)
  fsubs 11,11,10
  fmadds 10,11,12,10
  stfs 10,{RY_OFF}(8)
  b writecur

fpsnocam:
  stfs 8,{RX_OFF}(8)
  stfs 8,{RY_OFF}(8)
writecur:
  lfs 11,{RX_OFF}(8)
  stfs 11,0x20(29)
  lfs 11,{RY_OFF}(8)
  lfs 13,{KO['SY']}(7)
  fmuls 11,11,13
  stfs 11,0x24(29)
  lis 10,{hi(CURSOR_BASE)}
  lwz 10,{lo(CURSOR_BASE)}(10)
{neg_ptr(10,'nocursor')}  lwz 10,0xc54(10)
{neg_ptr(10,'nocursor')}  lfs 11,{RX_OFF}(8)
  stfs 11,0x9c(10)
  lfs 11,{RY_OFF}(8)
  lfs 13,{KO['SY']}(7)
  fmuls 11,11,13
  stfs 11,0x15c(10)
nocursor:
  mftb 6
  stw 6,{LAST_OFF}(8)
  li 3,2
  b setdpd

visormode:
  fmuls 9,3,3
  fmadds 9,4,4,9
  li 3,2
  lfs 10,{POS_OFF}(8)
  stfs 9,{POS_OFF}(8)
  lwz 12,{POS_OFF+4}(8)
  fcmpu 0,9,10
  bgt vunfreeze
  lfs 11,{KO['VDROP']}(7)
  fmuls 11,10,11
  fcmpu 0,9,11
  bge vchk
  li 12,1
  b vstore
vunfreeze:
  li 12,0
vstore:
  stw 12,{POS_OFF+4}(8)
vchk:
  cmpwi 12,0
  bne vsnap
  lfs 10,{KO['DZ2']}(7)
  fcmpu 0,9,10
  bge vfree
vsnap:
  lfs 8,{KO['ZERO']}(7)
  lfs 9,{PX_OFF}(8)
  lfs 10,{PY_OFF}(8)
  fmuls 3,9,9
  fmadds 3,10,10,3
  lfs 11,{KO['VSX']}(7)
  fneg 12,11
  fsel 11,9,11,12
  lfs 12,{KO['VSY']}(7)
  fsubs 5,9,11
  fmuls 5,5,5
  fsubs 6,10,12
  fmadds 5,6,6,5
  lfs 13,{KO['VTY']}(7)
  fsubs 6,10,13
  fmuls 6,6,6
  fmadds 6,9,9,6
  fsubs 0,6,5
  fsel 4,0,5,6
  fsel 9,0,11,8
  fsel 10,0,12,13
  fsubs 0,3,4
  fsel 9,0,9,8
  fsel 10,0,10,8
  stfs 9,{PX_OFF}(8)
  stfs 10,{PY_OFF}(8)
  b pset
vfree:
  lfs 5,{KO['ONE']}(7)
  lfs 6,{KO['SY']}(7)
  fmuls 3,3,5
  fmuls 4,4,6
  stfs 3,{PX_OFF}(8)
  stfs 4,{PY_OFF}(8)
  b pset
ptrmode:
  lis 12,{hi(STATE_MANAGER)}
  lwz 12,{lo(STATE_MANAGER)}(12)
  cmpwi 12,0
  bge notmap
  lwz 12,0x2184(12)
  cmpwi 12,0
  bge notmap
  # v0.16c: in map: WM 2 (dpad up) -> + (zoom in), WM up (classic dpad down) -> - (zoom out),
  # WM + (classic minus) -> 2 (hint), WM - (ZL) dropped
  # v0.16f: classic + also sends WM +; drop it here so it does not become the hint (2)
  # v0.18c: ya no hace falta quitar el + del Wiimote: un toque de + no lo manda
  li 11,0
mapbtn:
  lwzx 12,29,11
  rlwinm 3,12,28,27,27
  rlwinm 0,12,4,23,23
  or 3,3,0
  rlwinm 0,12,9,19,19
  or 3,3,0
  li 0,0x1118
  andc 12,12,0
  or 12,12,3
  stwx 12,29,11
  addi 11,11,4
  cmpwi 11,8
  blt mapbtn
  lwz 12,{V_CLHOLD}(8)
  lwz 0,{MLOCK_OFF}(7)
  and. 0,12,0
  li 3,2
  beq mapnoz
  fmuls 9,1,1
  fmadds 9,2,2,9
  lfs 10,{KO['DZ2']}(7)
  fcmpu 0,9,10
  bge pset
  lwz 12,0(29)
  rlwinm 12,12,0,19,17
  stw 12,0(29)
  lwz 12,4(29)
  rlwinm 12,12,0,19,17
  stw 12,4(29)
  stfs 3,0x60(29)
  stfs 4,0x64(29)
  b pset
mapnoz:
  stfs 3,0x60(29)
  stfs 4,0x64(29)
notmap:
  mftb 6
  li 3,2
pleft:
  fmuls 9,1,1
  fmadds 9,2,2,9
  lfs 13,{KO['DZ2']}(7)
  fcmpu 0,9,13
  bge pmove
  lfs 9,{KO['ZERO']}(7)
  stfs 9,{VX_OFF}(8)
  stfs 9,{VY_OFF}(8)
  b pidle
pmove:
  fsubs 10,9,7
  fsel 9,10,7,9
  lfs 13,{KO['MCUR']}(7)
  lfs 10,{KO['MBASE']}(7)
  fmadds 9,9,13,10
  lfs 13,{KO['MSENS']}(7)
  fmuls 9,9,13
  lfs 13,{KO['MSM']}(7)
  lfs 12,{KO['MSX']}(7)
  fmuls 10,1,12
  fmuls 10,10,9
  lfs 11,{VX_OFF}(8)
  fsubs 12,10,11
  fmadds 11,12,13,11
  stfs 11,{VX_OFF}(8)
  lfs 10,{PX_OFF}(8)
  fadds 10,10,11
  lfs 12,{KO['MLX']}(7)
  fsubs 11,12,10
  fsel 10,11,10,12
  fneg 11,12
  fsubs 12,10,11
  fsel 10,12,10,11
  stfs 10,{PX_OFF}(8)
  lfs 12,{KO['MSY']}(7)
  fmuls 10,2,12
  fmuls 10,10,9
  lfs 11,{VY_OFF}(8)
  fsubs 12,10,11
  fmadds 11,12,13,11
  stfs 11,{VY_OFF}(8)
  lfs 10,{PY_OFF}(8)
  fadds 10,10,11
  fsubs 11,7,10
  fsel 10,11,10,7
  fneg 11,7
  fsubs 12,10,11
  fsel 10,12,10,11
  stfs 10,{PY_OFF}(8)
  stw 6,{LAST_OFF}(8)
  b pset
pidle:
  # v0.11e: no idle-hide in menus
pset:
  lfs 9,{PX_OFF}(8)
  stfs 9,0x20(29)
  lfs 9,{PY_OFF}(8)
  stfs 9,0x24(29)
setdpd:
  stb 3,0x5e(29)
end:
  lfs 0,0xbf0(28)
"""

enc, _ = ks.asm(asm, 0)
b = bytes(enc)
words = [b[i:i+4] for i in range(0, len(b), 4)]
if len(words) % 2 == 0: words.append(bytes.fromhex('60000000'))
words.append(b'\0' * 4)

code = []
# v0.16d: escrituras consecutivas agrupadas en un código 06 (ahorra espacio)
_pw = sorted([EXT_PATCH] + STATIC + MOTION)
assert len({a for a, _ in _pw}) == len(_pw)
_runs = []
for a, v in _pw:
    if _runs and _runs[-1][0] + 4*len(_runs[-1][1]) == a: _runs[-1][1].append(v)
    else: _runs.append((a, [v]))
for a, vs in _runs:
    if len(vs) < 4:
        code += [f"{0x04000000 | (a + 4*k) & 0x1ffffff:08X} {v:08X}" for k, v in enumerate(vs)]
    else:
        bs = b''.join(struct.pack('>I', v) for v in vs); n = len(bs); bs += b'\0' * (-n % 8)
        code.append(f"{0x06000000 | a & 0x1ffffff:08X} {n:08X}")
        code += [f"{bs[k:k+4].hex().upper()} {bs[k+4:k+8].hex().upper()}" for k in range(0, len(bs), 8)]
sw = SHAKE_ASM + [0x60000000] * (1 - len(SHAKE_ASM) % 2) + [0]
code.append(f"C2{SHAKE_HOOK & 0x1ffffff:06X} {len(sw)//2:08X}")
code += [f"{sw[i]:08X} {sw[i+1]:08X}" for i in range(0, len(sw), 2)]
# v1.0: menú HOME de la Wii. En 0x800CDDF0 (lwz r12,0x50(r30): puntero a HBMUpdate, solo con el menú abierto)
# apuntamos el time base en VAR+0x8C; el gancho principal no toca el mando mientras tanto (controles normales).
HBM_HOOK = 0x800cddf0
hw = A1(f"lis 3,0x{VAR>>16:x}; mftb 12; stw 12,{(VAR&0xffff)+V_HBMT}(3); lwz 12,0x50(30)")
hw = hw + [0x60000000] * (1 - len(hw) % 2) + [0]
code.append(f"C2{HBM_HOOK & 0x1ffffff:06X} {len(hw)//2:08X}")
code += [f"{hw[i]:08X} {hw[i+1]:08X}" for i in range(0, len(hw), 2)]
hk = b''.join(struct.pack('>I', w) for w in CTRL_HOOK)
code.append(f"{0x06000000 | CTRL_HOOK_ADDR & 0x1ffffff:08X} {len(hk):08X}")
for i in range(0, len(hk), 8): code.append(f"{hk[i:i+4].hex().upper()} {hk[i+4:i+8].hex().upper()}")
code.append(f"C2{HOOK & 0x1ffffff:06X} {len(words)//2:08X}")
code += [f"{words[i].hex().upper()} {words[i+1].hex().upper()}" for i in range(0, len(words), 2)]

# --- Código aparte: mantener + 1 s salta la cinemática ----------------------------
# El juego salta una cinemática con la orden interna 0x3D del ControlMapper (en 0x800E0E18 llama a
# 0x800625C4 con r4 = 0x3D), si la cinemática es saltable (bit 0x80 de +0x65D, que viene de 0x800BBD24).
# Hacemos que 0x800BBD24 devuelva 1 (todas saltables, como PrimeHack) y que la orden valga 1 tras 2 s con +.
SKIP_HOLD_S = 1.0
_t = int(SKIP_HOLD_S * TB)
skip_asm = f'''
  lis 12,0x8006
  ori 12,12,0x25c4
  mtctr 12
  bctrl
  lis 12,0x{VAR>>16:x}
  ori 12,12,0x{VAR&0xffff:x}
  mftb 10
  stw 10,{V_CUTT}(12)
  lwz 11,{V_CLHOLD}(12)
  andi. 11,11,0x{CL['PLUS']:x}
  beq noplus
  lwz 11,{V_SKIPON}(12)
  cmpwi 11,0
  bne have
  stw 10,{V_SKIPT}(12)
  li 11,1
  stw 11,{V_SKIPON}(12)
have:
  lwz 11,{V_SKIPT}(12)
  subf 10,11,10
  lis 11,0x{_t>>16:x}
  ori 11,11,0x{_t&0xffff:x}
  cmplw 10,11
  blt done
  li 3,1
  b done
noplus:
  li 11,0
  stw 11,{V_SKIPON}(12)
done:
'''
_e, _ = ks.asm(skip_asm, 0); _sb = bytes(_e); _sw = [_sb[i:i+4] for i in range(0, len(_sb), 4)]
if len(_sw) % 2 == 0: _sw.append(bytes.fromhex('60000000'))
_sw.append(b'\0' * 4)
skip_code = ["040BBD24 38600001", "040BBD28 4E800020", f"C20E0E18 {len(_sw)//2:08X}"] + \
            [f"{_sw[i].hex().upper()} {_sw[i+1].hex().upper()}" for i in range(0, len(_sw), 2)]
SKIP_NAME = "$Skip cutscenes (hold + 1 s)"
open('saltar_cinematicas.txt', 'w').write('\n'.join(skip_code) + '\n')

open('code.txt', 'w').write('\n'.join(code) + '\n')
gct = bytes.fromhex('00D0C0DE00D0C0DE') + b''.join(bytes.fromhex(l.replace(' ', '')) for l in code) + bytes.fromhex('F000000000000000')
skip_bytes = b''.join(bytes.fromhex(l.replace(' ', '')) for l in skip_code)
open('RM3P01.gct', 'wb').write(gct[:-8] + skip_bytes + gct[-8:])
# v0.16g: Dolphin copia los códigos a 0x80002338 y no pasan de 0x80003000 (3272 bytes con cabecera y final);
# si se pasa, el último código (saltar cinemáticas) se queda fuera sin avisar.
GCT_LIMIT = 0x80003000 - 0x80002338
assert len(gct) + len(skip_bytes) <= GCT_LIMIT, f'GCT demasiado grande: {len(gct)+len(skip_bytes)} > {GCT_LIMIT}'   # la Wii carga todos los códigos del .gct
with open('RM3P01.ini', 'w') as f:
    f.write(f"[Gecko]\n$Classic Controller {VERSION}\n" + '\n'.join(code) + f"\n{SKIP_NAME}\n" + '\n'.join(skip_code) +
            f"\n[Gecko_Enabled]\n$Classic Controller {VERSION}\n{SKIP_NAME}\n")

if __name__ == '__main__':
    md = capstone.Cs(capstone.CS_ARCH_PPC, capstone.CS_MODE_32 | capstone.CS_MODE_BIG_ENDIAN | capstone.CS_MODE_PS); md.skipdata = True
    for i in md.disasm(b, 0): print(f'{i.address:04x}: {i.mnemonic} {i.op_str}')

# --- Plantilla para el configurador (configurador.html) ------------------------
import json
_c2 = next(i for i, l in enumerate(code) if l.startswith(f"C2{HOOK & 0x1ffffff:06X}"))
_table = 8 + (_c2 + 1) * 8 + 76          # cabecera GCT + líneas previas + línea C2 + 19 instrucciones (v1.0)
assert gct[_table:_table+4] == struct.pack('>I', TABLE[0][0])
json.dump({
    'version': VERSION, 'gct': gct.hex(), 'table': _table, 'nslot': NSLOT,
    'mlock': _table + N*8 + MLOCK_OFF, 'mlasso': _table + N*8 + MLASSO_OFF, 'mshake': _table + N*8 + MSHAKE_OFF,
    'skip': skip_bytes.hex(), 'skipname': SKIP_NAME, 'skiplines': skip_code,
    'CL': CL, 'WM': WM, 'map': MAP, 'lock': LOCK_BTN, 'lasso': LASSO_BTN, 'shake': SHAKE_BTN,
}, open('template.json', 'w'))
