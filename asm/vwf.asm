; English VWF for the one string renderer (0x80102D90, 113 callers): docs/re/font.md §VWF.
; Single bytes 0x01-0xBF with a non-zero VWF_WIDTH entry draw the page-0 font cell VWF_CODE[byte] (an SJIS code,
; 0 = advance only, e.g. space) and advance the pen by the width. Every other single byte keeps its old meaning
; (0x00 end, 0x0A newline, b h m r w z control letters, the rest skipped).
; Built by build.py: armips asm/vwf.asm -equ EXE "<path>" -equ TABLES "<path to vwf_tables.asm>"
.psx
.open EXE, 0x800A5800                   ; PS-X EXE: RAM = 0x800A5800 + file offset (header included)

VWF_FREE      equ 0x8016D740            ; exe zero run 0x8016D740-0x8016DC3F (trap-tested, docs/re/font.md)
VWF_FREE_END  equ 0x8016DA60            ; 0x8016DA60-0x8016DC3F holds moved exe strings (tools/insert.py EXE_FREE)
GLYPH_TABLE   equ 0x8015711C
GLYPH_FIND    equ 0x80103174            ; (a0 code, a1 first row, a2 last row) -> entry index or -1
CLUT_ID       equ 0x801444E4
DEC_TAIL      equ 0x80103624            ; sets u, v, w=12, h=12 from s4 code, v1 first code, s0 entry
DEC_RET       equ 0x8010374C            ; return s1

; --- decoder 0x8010329C: single-byte path ----------------------------------------------------------------------
.org 0x8010365C
  j     vwf_byte
  nop

; --- caller: pen advance after a drawn glyph. Types 0x14-0x17 (8px font) +8 as before; 0x18+w: +w -------------
.org 0x801030F4
  lhu   v1, 0x3E(sp)
  slti  v0, s3, 0x14
  bnez  v0, 0x80103118                  ; 0xC-0x13: no advance
  addiu v0, s3, -0x18
  bgez  v0, 0x80103114                  ; VWF glyph: x += type - 0x18
  addu  v0, v1, v0
  addiu v0, v1, 8
  nop
.if org() != 0x80103114
  .error "advance patch size"
.endif

.org VWF_FREE
vwf_byte:                               ; a0 byte, s1 -1, s2 sprite, s3 pen state, s5 font info
  sltiu v0, a0, 0xC0
  beqz  v0, @@orig
  nop
  lui   t0, hi(VWF_WIDTH)
  addu  t0, t0, a0
  lbu   v0, lo(VWF_WIDTH)(t0)
  sll   t1, a0, 1
  beqz  v0, @@orig
  lui   t0, hi(VWF_CODE)
  addu  t0, t0, t1
  lhu   s4, lo(VWF_CODE)(t0)
  addiu s1, v0, 0x18                    ; return type 0x18 + width
  bnez  s4, @@glyph
  nop
  lhu   t0, 6(s3)                       ; no glyph: advance only, nothing drawn (type 1, like 0x8140)
  addiu s1, zero, 1
  addu  t0, t0, v0
  j     DEC_RET
  sh    t0, 6(s3)
@@glyph:
  move  a0, s4
  move  a1, zero
  jal   GLYPH_FIND
  addiu a2, zero, 0x14
  bgez  v0, @@found
  move  v1, v0
  j     DEC_RET
  addiu s1, zero, -1
@@found:                                ; as 0x80103570-0x801035B4
  lui   t0, hi(GLYPH_TABLE)
  addiu t0, t0, lo(GLYPH_TABLE)
  sll   s0, v1, 1
  addu  s0, s0, v1
  sll   s0, s0, 1
  addu  s0, s0, t0
  lbu   v1, 2(s0)
  lhu   v0, 8(s5)
  addiu a0, zero, 0x100
  addu  v0, v0, v1
  sh    v0, 0(s2)
  lhu   a1, 4(s3)
  lbu   v0, 4(s0)
  addiu a1, a1, 0x1E0
  jal   CLUT_ID
  addu  a1, v0, a1
  sh    v0, 2(s2)
  lhu   v1, 0(s0)
  j     DEC_TAIL
  nop
@@orig:                                 ; the two instructions the hook replaced
  addiu v0, zero, 0x6D
  bne   a0, v0, @@not_m
  move  s1, zero
  j     0x8010372C                      ; 'm'
  nop
@@not_m:
  j     0x80103668
  nop

.align 2
.include TABLES                         ; VWF_WIDTH: .byte x 0xC0, VWF_CODE: .halfword x 0xC0 (tools/font.py)
.if org() > VWF_FREE_END
  .error "VWF code and tables overflow the free run"
.endif
.close
