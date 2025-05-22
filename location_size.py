class l_and_s():
    def __init__(self,x=0,y=0,weight=0,height=0,fontsize=0) -> None:
        self.x=x
        self.y=y
        self.weight=weight
        self.height=height
        if type(weight)!=type(Ellipsis):
            self.xe=x+weight
            self.ye=y+height
        self.fontsize=fontsize
    @property
    def l(self):
        return self.x,self.y
    @property
    def s(self):
        return self.weight,self.height
    @property
    def r(self):
        return self.x,self.y,self.weight,self.height
window=l_and_s(0,0,420,540)
window2=l_and_s(0,0,760,540)

surface_1=l_and_s(0,0,420,540)
title=l_and_s(180,10,1000,50,fontsize=30)
cover=l_and_s(60,70,300,300)

time_left=l_and_s(10,420,fontsize=20)
time_right=l_and_s(360,420,fontsize=20)

font_state=l_and_s(fontsize=12)
font_s0_name=l_and_s(fontsize=10)

btn_pre=l_and_s(90,450,60,60)
btn_next=l_and_s(270,450,60,60)
btn_pause=l_and_s(170,440,80,80)
btn_vol=l_and_s(345,460,40,40)
vol_bar=l_and_s(362,388,6,64)
vol_block=l_and_s(355,380,20,80)
btn_mode=l_and_s(35,460,40,40)
btn_acc=l_and_s(10,20,60,30)
tab_bar=l_and_s(370,10,50,50)

btn_unpause=btn_pause
btn_prep=l_and_s(5,205,50,50)
btn_nextp=l_and_s(365,205,50,50)
# 波形
W_sam_T=0.1  # 窗口间隔，函数周期
W_sampling_rate=2400
W_CHUNK=int(W_sampling_rate*W_sam_T)
W_top=120*W_sam_T
W_bot=0*W_sam_T

lyricANDbar=l_and_s(0,370,420,70)
lyric=l_and_s(50,372,320,50,fontsize=20)
bar_l=l_and_s(68,428,284,8)
bar_s=l_and_s(70,429,280,6)


surface_2=l_and_s(420,0,window2.weight-surface_1.weight,540)
labal=l_and_s(420,0,window2.weight-surface_1.weight,50)
mainview=l_and_s(420,labal.height,window2.weight-surface_1.weight,window2.height-labal.height)


name_offset_x=5
name_offset_y=5
name_peritem=30
step=30
name=l_and_s(surface_1.weight+100+name_offset_x,mainview.y+name_offset_y)
info=l_and_s(window2.weight-80,5,18,18)


word_offset_x=5
word_offset_y=5
word_peritem=30
word_bars=l_and_s(surface_1.weight+100,mainview.y+5,230,20)
