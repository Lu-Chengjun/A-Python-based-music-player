# -*- coding: utf-8 -*-
import sys
import pygame
import time
import os
import re
from mutagen.mp3 import MP3
from tempfile import TemporaryFile
import location_size
import threading
import librosa
import numpy as np
import numpy.fft as fft
import jieba
import collections
import json
import random
from functools import reduce
import tkinter.messagebox
from tkinter import filedialog
os.chdir(os.path.dirname(__file__))

# 初始化 pygame
pygame.init()
pygame.mixer.init()

# 屏幕设置
screen = pygame.display.set_mode(location_size.window.s)
pygame.display.set_caption(r'音乐播放器')
screen.blit(pygame.transform.scale(pygame.image.load('icon/bg1.jpg'), location_size.surface_1.s), location_size.surface_1.l)

# Event 事件定义
class MusicEvents():
    def __init__(self):
        self.MUSIC_END = pygame.USEREVENT + 1
        self.SONG_CHANGE = pygame.USEREVENT + 2
        self.PAUSE = pygame.USEREVENT + 3
        self.UNPAUSE = pygame.USEREVENT + 4

music_events = MusicEvents()

# 音乐播放器主界面定义
class PlayerInterface():
    def __init__(self):
        self.wave_data = np.array((0, 0))
        self.wave_loaded = False
        self.volume_bar_visible = False
        self.wave_length = 0
        self.lyrics = []
        self.display_state = 0  # 0: cover, 1: spectrum, 2: both
        self.spectrum_bars = [0] * 60
        self.is_dragging_volume = False
        self.last_spectrum_update = 0
        self.is_dragging_progress = False
        self.time_font = pygame.font.SysFont("SimHei", location_size.time_left.fontsize)
        self.lyric_font = pygame.font.SysFont("SimHei", location_size.lyric.fontsize)
        self.title_font = pygame.font.SysFont("SimHei", location_size.title.fontsize)
        self.sidebar_visible = True
        
    def entry(self):
        pygame.mixer.music.set_volume(1.0)
        self.pause_img = pygame.transform.scale(pygame.image.load(r'icon\pause.png').convert_alpha(), location_size.btn_pause.s)
        self.play_img = pygame.transform.scale(pygame.image.load(r'icon\unpause.png').convert_alpha(), location_size.btn_unpause.s)
        self.pause_button = screen.blit(self.pause_img, location_size.btn_pause.l)
        
        try:
            song_title = str(getattr(player, 'tags',)['TIT2']).strip()
        except:
            song_title = str(os.path.split(player.playlist[player.current_index])[1][:-4])
            
        self.title_text = self.title_font.render(song_title, True, (0, 0, 0))
        location_size.title.x = (location_size.surface_1.weight - self.title_text.get_size()[0]) / 2
        
        try:
            with TemporaryFile(mode="wb+") as f:
                f.name = 'temp.jpeg'
                f.write(getattr(player, 'tags')['APIC:'].data)
                f.seek(0)
                self.album_art = pygame.transform.scale(pygame.image.load(f), location_size.cover.s)
        except:
            self.album_art = pygame.transform.scale(pygame.image.load(r'icon\record.png'), location_size.cover.s)
            
    def event(self, event):
        if event.type == music_events.SONG_CHANGE:
            self.handle_song_change()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_mouse_down(event)
        elif event.type == pygame.KEYDOWN:
            self.handle_key_press(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.handle_mouse_up(event)
            
    def handle_song_change(self):
        try:
            song_title = str(getattr(player, 'tags',)['TIT2']).strip()
        except:
            song_title = str(os.path.split(player.playlist[player.current_index])[1][:-4])
            
        self.title_text = self.title_font.render(song_title, True, (0, 0, 0))
        location_size.title.x = (location_size.surface_1.weight - self.title_text.get_size()[0]) / 2
        self.wave_loaded = False
        
        def load_wave_data():
            self.wave_data = librosa.load(player.playlist[player.current_index], sr=location_size.W_sampling_rate)[0]
            self.wave_length = len(self.wave_data)
            self.wave_loaded = True
            
        threading.Thread(target=load_wave_data, daemon=True).start()
        
        try:
            with TemporaryFile(mode="wb+") as f:
                f.name = 'temp.jpeg'
                f.write(getattr(player, 'tags')['APIC:'].data)
                f.seek(0)
                self.album_art = pygame.transform.scale(pygame.image.load(f), location_size.cover.s)
        except:
            self.album_art = pygame.transform.scale(pygame.image.load(r'icon\record.png'), location_size.cover.s)
            
        self.lyrics = []
        try:
            raw_lyrics = str(getattr(player, 'tags',)['USLT::   '])
        except:
            raw_lyrics = ''
        for line in raw_lyrics.split('\n'):
            if match := re.match(r'\[(\d\d):(\d\d\.\d\d)\](.*)', line):
                minutes, seconds, text = match.groups()
                self.lyrics.append((int(minutes) * 60 + float(seconds), text))
                
        try:
            lyrics_text = reduce(lambda x, y: x + ' ' + y, map(lambda x: x[1], self.lyrics))
            word_counts = collections.Counter(list(jieba.cut(lyrics_text)))
            filtered_words = filter(lambda key: len(key[0].strip()) > 1 and 
                                  0x4E00 <= ord(key[0][0]) <= 0x9FA5 or 
                                  0x9FA6 <= ord(key[0][0]) <= 0x9FFF or 
                                  0x3400 <= ord(key[0][0]) <= 0x4DBF or 
                                  0x20000 <= ord(key[0][0]) <= 0x323AF, 
                                  word_counts.items())
            lyrics_sidebar.word_list = sorted(filtered_words, key=lambda n: n[1], reverse=True)
        except:
            lyrics_sidebar.word_list = [('NULL', 1)]
            
        self.current_lyric_index = 0
        
    def handle_mouse_down(self, event):
        if event.button == 1:  # Left click
            if self.volume_bar_visible and self.volume_bar.collidepoint(event.pos):
                self.is_dragging_volume = True
            elif self.progress_bar.collidepoint(event.pos):
                self.is_dragging_progress = True
                
    def handle_key_press(self, event):
        if event.key == pygame.K_SPACE:
            player.pause() if player.is_playing else player.unpause()
        elif event.key == pygame.K_DOWN:
            player.decrease_volume()
        elif event.key == pygame.K_UP:
            player.increase_volume()
            
    def handle_mouse_up(self, event):
        if event.button == 1:  # Left click
            if self.is_dragging_progress:
                progress = (event.pos[0] - location_size.bar_s.x) / location_size.bar_s.weight
                seek_time = progress * player.song_info.length
                player.seek(max(0, min(seek_time, player.song_info.length)))
                self.is_dragging_progress = False
            elif self.volume_bar_visible:
                self.is_dragging_volume = False
                if not self.volume_slider.collidepoint(event.pos):
                    self.volume_bar_visible = False
            elif self.accompaniment_button.collidepoint(event.pos) and self.accompaniment_button.collidepoint(MOUSE_DOWN_POS):
                player.toggle_accompaniment()
            elif self.play_mode_button.collidepoint(event.pos) and self.play_mode_button.collidepoint(MOUSE_DOWN_POS):
                player.change_play_mode()
            elif self.prev_state_button.collidepoint(event.pos) and self.prev_state_button.collidepoint(MOUSE_DOWN_POS):
                self.display_state = (self.display_state - 1) % 3
            elif self.next_state_button.collidepoint(event.pos) and self.next_state_button.collidepoint(MOUSE_DOWN_POS):
                self.display_state = (self.display_state + 1) % 3
            elif self.prev_button.collidepoint(event.pos) and self.prev_button.collidepoint(MOUSE_DOWN_POS):
                player.previous_song()
            elif self.next_button.collidepoint(event.pos) and self.next_button.collidepoint(MOUSE_DOWN_POS):
                player.next_song()
            elif self.volume_button.collidepoint(event.pos) and self.volume_button.collidepoint(MOUSE_DOWN_POS):
                self.volume_bar_visible = True
            elif self.pause_button.collidepoint(event.pos) and self.pause_button.collidepoint(MOUSE_DOWN_POS):
                if player.is_playing:
                    player.pause()
                else:
                    player.unpause()
            elif self.sidebar_button.collidepoint(event.pos) and self.sidebar_button.collidepoint(MOUSE_DOWN_POS):
                if self.sidebar_visible:
                    lyrics_sidebar.entry()
                    pygame.display.set_mode(location_size.window2.s)
                else:
                    lyrics_sidebar.exit()
                    pygame.display.set_mode(location_size.window.s)
                self.loop()
                self.sidebar_visible = not self.sidebar_visible
                
        elif event.button in (4, 5):  # Mouse wheel
            if self.volume_bar_visible:
                volume_up = event.button == 4
                player.increase_volume() if volume_up else player.decrease_volume()
                
    def loop(self):
        screen.blit(pygame.transform.scale(pygame.image.load('icon/bg1.jpg'), location_size.surface_1.s), location_size.surface_1.r)
        
        # Main display area
        if self.display_state in (0,2):  # Album art only
            screen.blit(self.album_art, location_size.cover.l)
        if self.display_state in (1,2):  # Spectrum or both
            current_time = time.time()
            if (current_time - BASE_TIME) // (location_size.W_sam_T / 2) > self.last_spectrum_update:
                if self.wave_loaded:
                    self.spectrum_bars = []
                    self.last_spectrum_update = current_time
                    self.last_spectrum_update = 0
                    try:
                        start_pos = int(player.get_position() * location_size.W_sampling_rate)
                        if start_pos + location_size.W_CHUNK < self.wave_length:
                            audio_segment = self.wave_data[start_pos:start_pos + location_size.W_CHUNK]
                            spectrum = fft.rfft(audio_segment)
                            for i in range(60):
                                self.spectrum_bars.append(sum(spectrum[2*i:2*(i+1)]) * 5)
                        else:
                            self.spectrum_bars = [0] * 60
                    except:
                        self.spectrum_bars = [0] * 60
                else:
                    self.spectrum_bars = [0] * 60
                    
            # Draw spectrum bars
            for i, bar_height in enumerate(self.spectrum_bars):
                x_pos = 1 + 60 + 5 * i
                pygame.draw.rect(screen, (0, 0, 0), (x_pos, 300 - abs(bar_height), 3, int(abs(bar_height) + 1)))
                pygame.draw.rect(screen, (100, 100, 100), (x_pos, 300, 3, int(abs(0.15 * bar_height))))
                
        # Song title
        screen.blit(self.title_text, location_size.title.l, (0, 0, *location_size.title.s))
        
        # Control buttons
        self.prev_button = screen.blit(pygame.transform.scale(
            pygame.image.load(r'icon\pre.png').convert_alpha(), 
            location_size.btn_pre.s), location_size.btn_pre.l)
            
        self.next_button = screen.blit(pygame.transform.scale(
            pygame.image.load(r'icon\next.png').convert_alpha(), 
            location_size.btn_next.s), location_size.btn_next.l)
            
        self.prev_state_button = screen.blit(pygame.transform.scale(
            pygame.image.load(r'icon\prep.png').convert_alpha(), 
            location_size.btn_prep.s), location_size.btn_prep.l)
            
        self.next_state_button = screen.blit(pygame.transform.scale(
            pygame.image.load(r'icon\nextp.png').convert_alpha(), 
            location_size.btn_nextp.s), location_size.btn_nextp.l)
            
        volume_icon = r'icon\volume.png' if pygame.mixer.music.get_volume() != 0 else r'icon\volume_n.png'
        self.volume_button = screen.blit(pygame.transform.scale(
            pygame.image.load(volume_icon).convert_alpha(), 
            location_size.btn_vol.s), location_size.btn_vol.l)
            
        self.pause_button = screen.blit(
            self.pause_img if player.is_playing else self.play_img, 
            (170, 440))
            
        self.play_mode_button = screen.blit(pygame.transform.scale(
            pygame.image.load(f'icon\\mode{player.play_mode}.png').convert_alpha(), 
            location_size.btn_mode.s), location_size.btn_mode.l)
            
        # Time display
        total_time = self.time_font.render(
            f'{str(int(player.song_info.length // 60)).rjust(2, "0")}:{str(int(player.song_info.length % 60)).rjust(2, "0")}', 
            True, (0, 0, 0))
        screen.blit(total_time, (location_size.surface_1.weight - location_size.time_left.x - total_time.get_size()[0], 
                                location_size.time_right.y))
                                
        # Sidebar toggle button
        sidebar_icon = r'icon\tab_bar_1.png' if self.sidebar_visible else r'icon\tab_bar.png'
        self.sidebar_button = screen.blit(pygame.transform.scale(
            pygame.image.load(sidebar_icon).convert_alpha(), 
            location_size.tab_bar.s), location_size.tab_bar.l)
            
        # Accompaniment button
        accompaniment_available = False
        if os.path.exists(player.music_folder + '/伴奏'):
            for file in os.listdir(player.music_folder + '/伴奏'):
                try:
                    if str(getattr(player, 'tags')['TIT2']) in file and '伴奏' in file:
                        accompaniment_available = True
                        if player.is_accompaniment:
                            icon = r'icon\acc_T.png'
                            text = '打开人声'
                        else:
                            icon = r'icon\acc_F.png'
                            text = '关闭人声'
                        self.accompaniment_button = screen.blit(pygame.transform.scale(
                            pygame.image.load(icon).convert_alpha(), 
                            location_size.btn_acc.s), location_size.btn_acc.l)
                        screen.blit(lyrics_sidebar.small_font.render(text, True, (0, 0, 0)), 
                                  (location_size.btn_acc.x + 10, location_size.btn_acc.y + 8))
                        break
                except:
                    pass
                    
        if not accompaniment_available:
            self.accompaniment_button = screen.blit(pygame.transform.scale(
                pygame.image.load(r'icon\acc_N.png').convert_alpha(), 
                location_size.btn_acc.s), location_size.btn_acc.l)
            screen.blit(lyrics_sidebar.small_font.render('暂无伴奏', True, (0, 0, 0)), 
                      (location_size.btn_acc.x + 10, location_size.btn_acc.y + 8))
                      
        # Progress bar
        if self.is_dragging_progress:
            self.progress_bar = pygame.draw.rect(screen, (0, 0, 0), location_size.bar_l.r)
            mouse_x = pygame.mouse.get_pos()[0]
            progress = (mouse_x - location_size.bar_s.x) / location_size.bar_s.weight
            progress = max(0, min(progress, 1))
            pygame.draw.rect(screen, (255, 255, 255), 
                           (location_size.bar_s.x, location_size.bar_s.y, 
                            int(progress * location_size.bar_s.weight), location_size.bar_s.height))
                            
            current_time = progress * player.song_info.length
            minutes = int(current_time // 60)
            seconds = int(current_time % 60)
            time_text = self.time_font.render(f'{str(minutes).rjust(2, "0")}:{str(seconds).rjust(2, "0")}', 
                                            True, (0, 0, 0))
            screen.blit(time_text, location_size.time_left.l)
            
            # Update lyrics display
            self.update_lyrics_display(current_time)
        else:
            current_time = player.get_position()
            self.progress_bar = pygame.draw.rect(screen, (0, 0, 0), location_size.bar_l.r)
            progress = current_time / player.song_info.length
            pygame.draw.rect(screen, (255, 255, 255), 
                           (location_size.bar_s.x, 429, 
                            int(location_size.bar_s.weight * progress), 6))
                            
            minutes = int(current_time // 60)
            seconds = int(current_time % 60)
            time_text = self.time_font.render(f'{str(minutes).rjust(2, "0")}:{str(seconds).rjust(2, "0")}', 
                                            True, (0, 0, 0))
            screen.blit(time_text, (10, 420))
            
            # Update lyrics display
            self.update_lyrics_display(current_time)
            
        # Volume control
        if self.volume_bar_visible:
            self.volume_slider = pygame.draw.rect(screen, (0, 0, 0), location_size.vol_block.r)
            self.volume_bar = pygame.draw.rect(screen, (255, 255, 255), location_size.vol_bar.r)
            
            if self.is_dragging_volume:
                mouse_y = pygame.mouse.get_pos()[1]
                volume_height = location_size.vol_bar.y + location_size.vol_bar.height - mouse_y
                volume_height = max(0, min(volume_height, location_size.vol_bar.height))
                pygame.draw.rect(screen, (0, 0, 200), 
                               (location_size.vol_bar.x, 
                                location_size.vol_bar.y + location_size.vol_bar.height - volume_height, 
                                location_size.vol_bar.weight, 
                                volume_height))
                pygame.mixer.music.set_volume(volume_height / location_size.vol_bar.height)
            else:
                current_volume = pygame.mixer.music.get_volume()
                volume_height = int(location_size.vol_bar.height * current_volume)
                pygame.draw.rect(screen, (0, 0, 200), 
                               (location_size.vol_bar.x, 
                                location_size.vol_bar.y + location_size.vol_bar.height - volume_height, 
                                location_size.vol_bar.weight, 
                                volume_height))
                                
    def update_lyrics_display(self, current_time):
        if not self.lyrics:
            screen.blit(self.lyric_font.render('暂无歌词', True, (0, 0, 0)), 
                      location_size.lyric.l, (0, 0, *location_size.lyric.s))
            return
                      
        if current_time < self.lyrics[0][0]:
            screen.blit(self.lyric_font.render(self.lyrics[0][1], True, (0, 0, 0)), 
                      location_size.lyric.l, (0, 0, *location_size.lyric.s))
            self.current_lyric_index = 0
        else:
            for i in range(self.current_lyric_index + 1, len(self.lyrics)):
                if current_time < self.lyrics[i][0]:
                    screen.blit(self.lyric_font.render(self.lyrics[i-1][1], True, (0, 0, 0)), 
                              location_size.lyric.l, (0, 0, *location_size.lyric.s))
                    self.current_lyric_index = i - 1
                    break
            else:
                self.current_lyric_index = len(self.lyrics) - 1
                screen.blit(self.lyric_font.render(self.lyrics[-1][1], True, (0, 0, 0)), 
                          location_size.lyric.l, (0, 0, *location_size.lyric.s))

# 侧边栏界面定义
class LyricsSidebar():
    def __init__(self):
        self.is_visible = False
        self.tab_states = ['播放列表', '歌词分析', '歌单']
        self.show_info_dialog = True
        self.current_tab = 0
        self.word_list = []
        self.background = pygame.draw.rect(screen, (245, 245, 255), location_size.surface_2.r)
        self.tab_font = pygame.font.SysFont("SimHei", location_size.font_state.fontsize)
        self.small_font = pygame.font.SysFont("SimHei", location_size.font_s0_name.fontsize)
        
        # Tab buttons
        self.playlist_tab = pygame.draw.rect(
            screen, (225, 225, 255) if self.current_tab == 0 else (255, 255, 255),
            (location_size.labal.x, location_size.labal.y, location_size.labal.weight // 3, location_size.labal.height))
            
        self.lyrics_tab = pygame.draw.rect(
            screen, (225, 225, 255) if self.current_tab == 1 else (255, 255, 255),
            (location_size.labal.x + location_size.labal.weight // 3, location_size.labal.y, 
             location_size.labal.weight // 3, location_size.labal.height))
             
        self.playlists_tab = pygame.draw.rect(
            screen, (225, 225, 255) if self.current_tab == 2 else (255, 255, 255),
            (location_size.labal.x + location_size.labal.weight * 2 // 3, location_size.labal.y, 
             location_size.labal.weight // 3, location_size.labal.height))
             
        self.playlist_scroll = 0
        self.lyrics_scroll = 0
        self.playlists_scroll = 0
        
    def entry(self):
        self.is_visible = True
        
    def exit(self):
        self.is_visible = False
        
    def loop(self):
        if not self.is_visible:
            return
            
        self.background = pygame.draw.rect(screen, (245, 245, 255), location_size.surface_2.r)
        
        if self.current_tab == 0:  # Playlist
            self.draw_playlist()
        elif self.current_tab == 1:  # Lyrics analysis
            self.draw_lyrics_analysis()
        elif self.current_tab == 2:  # Playlists
            self.draw_playlists()
            
        # Draw tab bar
        self.tab_bar = pygame.draw.rect(screen, (0, 0, 20), location_size.labal.r)
        
        # Update tab buttons
        self.playlist_tab = pygame.draw.rect(
            screen, (225, 225, 255) if self.current_tab == 0 else (255, 255, 255),
            (location_size.labal.x, location_size.labal.y, location_size.labal.weight // 3, location_size.labal.height))
            
        self.lyrics_tab = pygame.draw.rect(
            screen, (225, 225, 255) if self.current_tab == 1 else (255, 255, 255),
            (location_size.labal.x + location_size.labal.weight // 3, location_size.labal.y, 
             location_size.labal.weight // 3, location_size.labal.height))
             
        self.playlists_tab = pygame.draw.rect(
            screen, (225, 225, 255) if self.current_tab == 2 else (255, 255, 255),
            (location_size.labal.x + location_size.labal.weight * 2 // 3, location_size.labal.y, 
             location_size.labal.weight // 3, location_size.labal.height))
             
        # Draw tab labels
        playlist_label = self.tab_font.render(self.tab_states[0], True, (0, 0, 0))
        screen.blit(playlist_label, 
                   (location_size.surface_1.weight + (location_size.labal.weight / 3 - playlist_label.get_size()[0]) / 2, 10))
                   
        lyrics_label = self.tab_font.render(self.tab_states[1], True, (0, 0, 0))
        screen.blit(lyrics_label, 
                   (location_size.surface_1.weight + location_size.labal.weight / 3 + 
                    (location_size.labal.weight / 3 - lyrics_label.get_size()[0]) / 2, 10))
                    
        playlists_label = self.tab_font.render(self.tab_states[2], True, (0, 0, 0))
        screen.blit(playlists_label, 
                   (location_size.surface_1.weight + location_size.labal.weight * 2 / 3 + 
                    (location_size.labal.weight / 3 - playlists_label.get_size()[0]) / 2, 10))
                    
    def draw_playlist(self):
        for i, song_path in enumerate(player.playlist):
            y_pos = -self.playlist_scroll + (i + 1) * location_size.name_peritem + location_size.name_offset_y
            if y_pos > 0:
                song_name = os.path.split(song_path)[1]
                color = (0, 100, 0) if i == player.current_index else (0, 0, 0)
                screen.blit(self.tab_font.render(song_name, True, color),
                           (location_size.mainview.x + location_size.name_offset_x, 
                            -self.playlist_scroll + location_size.labal.height + i * location_size.name_peritem + location_size.name_offset_y))
                            
                # Info icon
                screen.blit(pygame.transform.scale(
                    pygame.image.load(r'icon\info.png').convert_alpha(), 
                    location_size.info.s),
                    (location_size.info.x, 
                     -self.playlist_scroll + location_size.labal.height + i * location_size.name_peritem + location_size.info.y))
                     
            if y_pos > location_size.window2.height:
                break
                
        end_text = self.tab_font.render('到底了', True, (0, 0, 0))
        screen.blit(end_text,
                   (location_size.mainview.x + 0.5 * location_size.mainview.weight - 0.5 * end_text.get_size()[0], 
                    -self.playlist_scroll + location_size.labal.height + len(player.playlist) * location_size.name_peritem + location_size.name_offset_y))
                    
    def draw_lyrics_analysis(self):
        # Top words section
        title = self.tab_font.render('————歌词中出现最多七个的词语————', True, (0, 0, 0))
        screen.blit(title,
                   (location_size.mainview.x + 0.5 * location_size.mainview.weight - 0.5 * title.get_size()[0], 
                    -self.lyrics_scroll + location_size.labal.height + 0 * location_size.word_peritem + location_size.word_offset_y))
                    
        for i, (word, count) in enumerate(self.word_list[:7] if len(self.word_list) >= 7 else [('Null', 1)] * 7):
            y_pos = -self.lyrics_scroll + location_size.labal.height + (i + 1) * location_size.word_peritem + location_size.word_offset_y
            screen.blit(self.tab_font.render(f'{word.strip()}:{count}', True, (0, 0, 0)),
                       (location_size.mainview.x + location_size.word_offset_x, y_pos))
                       
            # Word frequency bars
            if self.word_list:
                max_count = self.word_list[0][1]
                bar_width = int(location_size.word_bars.weight * count / max_count)
                pygame.draw.rect(screen, (225, 225, 255),
                               (location_size.word_bars.x, 
                                location_size.word_bars.y + (i + 1) * location_size.word_peritem - self.lyrics_scroll, 
                                bar_width, location_size.word_bars.height))
                                
        # Full lyrics section
        full_lyrics_title = self.tab_font.render('————歌词全文————', True, (0, 0, 0))
        screen.blit(full_lyrics_title,
                   (location_size.mainview.x + 0.5 * location_size.mainview.weight - 0.5 * full_lyrics_title.get_size()[0], 
                    -self.lyrics_scroll + location_size.labal.height + 8 * location_size.word_peritem + location_size.word_offset_y))
                    
        self.lyric_items = []
        current_line = 9  # Start after the headers
        
        for time_stamp, text in player_interface.lyrics:
            if text.strip() != '':
                # Time display
                minutes = int(time_stamp // 60)
                seconds = int(time_stamp % 60)
                time_text = self.tab_font.render(f'{str(minutes).rjust(2, "0")}:{str(seconds).rjust(2, "0")}', True, (0, 0, 0))
                screen.blit(time_text,
                           (location_size.mainview.x, 
                            -self.lyrics_scroll + location_size.labal.height + current_line * location_size.word_peritem + location_size.word_offset_y))
                            
                # Lyrics text (with ellipsis if too long)
                lyric_text = self.tab_font.render(text, True, (0, 0, 0))
                if lyric_text.get_size()[0] > location_size.mainview.weight - 2 * 50:
                    for j in range(len(text)):
                        shortened = text[:len(text) - j] + '. . .'
                        lyric_text = self.tab_font.render(shortened, True, (0, 0, 0))
                        if lyric_text.get_size()[0] < location_size.mainview.weight - 2 * 50:
                            break
                            
                screen.blit(lyric_text,
                           (location_size.mainview.x + 0.5 * location_size.mainview.weight - 0.5 * lyric_text.get_size()[0], 
                            -self.lyrics_scroll + location_size.labal.height + current_line * location_size.word_peritem + location_size.word_offset_y))
                            
                self.lyric_items.append(time_stamp)
                current_line += 1
                
        self.total_lyric_lines = current_line
        
    def draw_playlists(self):
        # Music sources section
        title = self.tab_font.render('————文件夹————', True, (0, 0, 0))
        screen.blit(title,
                   (location_size.mainview.x + 0.5 * location_size.mainview.weight - 0.5 * title.get_size()[0], 
                    -self.playlists_scroll + location_size.labal.height + 0 * location_size.word_peritem + location_size.word_offset_y))
                    
        self.playlist_commands:list = [None]  # Placeholder for the title
        
        folder_path = './music'
        if os.path.isdir(folder_path):
            color = (0, 150, 0) if "music" == os.path.split(player.music_folder)[-1] else (0, 0, 0)
            screen.blit(self.tab_font.render("music", True, color),
                        (location_size.mainview.x + location_size.word_offset_x, 
                        -self.playlists_scroll + location_size.labal.height + len(self.playlist_commands) * location_size.word_peritem + location_size.word_offset_y))
            self.playlist_commands.append((folder_path,))


        # Built-in music folders
        for folder in os.listdir('./music'):
            if folder in ("歌单","伴奏"):continue
            folder_path = './music/' + folder
            if os.path.isdir(folder_path):
                color = (0, 150, 0) if folder == os.path.split(player.music_folder)[-1] else (0, 0, 0)
                screen.blit(self.tab_font.render(folder, True, color),
                           (location_size.mainview.x + location_size.word_offset_x, 
                            -self.playlists_scroll + location_size.labal.height + len(self.playlist_commands) * location_size.word_peritem + location_size.word_offset_y))
                self.playlist_commands.append((folder_path,))
                
        # Additional folders
        for folder in player.additional_folders:
            if os.path.isdir(folder):
                color = (0, 150, 0) if folder == os.path.split(player.music_folder)[-1] else (0, 0, 0)
                screen.blit(self.tab_font.render(os.path.split(folder)[1], True, color),
                           (location_size.mainview.x + location_size.word_offset_x, 
                            -self.playlists_scroll + location_size.labal.height + len(self.playlist_commands) * location_size.word_peritem + location_size.word_offset_y))
                            
                # Remove button
                screen.blit(pygame.transform.scale(
                    pygame.image.load(r'icon\pop.png').convert_alpha(), 
                    location_size.info.s),
                    (location_size.info.x, 
                     -self.playlists_scroll + location_size.labal.height + len(self.playlist_commands) * location_size.name_peritem + location_size.info.y))
                     
                self.playlist_commands.append((folder, '\\', False))
                
        # Add folder button
        add_text = self.tab_font.render('点击添加文件夹', True, (150, 0, 150))
        screen.blit(add_text,
                   (location_size.mainview.x + 0.5 * location_size.mainview.weight - 0.5 * add_text.get_size()[0], 
                    -self.playlists_scroll + location_size.labal.height + len(self.playlist_commands) * location_size.word_peritem + location_size.word_offset_y))
        self.playlist_commands.append(lambda: player.additional_folders.append(filedialog.askdirectory()))
        
        # Playlists section
        playlists_title = self.tab_font.render('————歌单————', True, (0, 0, 0))
        screen.blit(playlists_title,
                   (location_size.mainview.x + 0.5 * location_size.mainview.weight - 0.5 * playlists_title.get_size()[0], 
                    -self.playlists_scroll + location_size.labal.height + (len(self.playlist_commands)) * location_size.word_peritem + location_size.word_offset_y))
        self.playlist_commands.append(None)  # Placeholder for the title
        
        # All songs option
        color = (0, 150, 0) if '\\' == player.current_playlist else (0, 0, 0)
        all_songs = self.tab_font.render('全部歌曲', True, color)
        screen.blit(all_songs,
                   (location_size.mainview.x + location_size.name_offset_x, 
                    -self.playlists_scroll + location_size.labal.height + (len(self.playlist_commands)) * location_size.name_peritem + location_size.name_offset_y))
        self.playlist_commands.append((player.music_folder,))
        
        # Custom playlists
        playlists_path = player.music_folder + '/歌单'
        if os.path.exists(playlists_path):
            for playlist_file in os.listdir(playlists_path):
                if playlist_file.endswith('.json'):
                    color = (0, 150, 0) if playlist_file == player.current_playlist else (0, 0, 0)
                    playlist_name = playlist_file[:-5]
                    screen.blit(self.tab_font.render(playlist_name, True, color),
                              (location_size.mainview.x + location_size.name_offset_x,
                               -self.playlists_scroll + location_size.labal.height + 
                               (len(self.playlist_commands)) * location_size.name_peritem + 
                               location_size.name_offset_y))
                    self.playlist_commands.append((player.music_folder, playlist_file))

    def event(self, event):
        if not self.is_visible:
            return
            
        if event.type == music_events.SONG_CHANGE:
            self.lyrics_scroll = 0
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.handle_mouse_click(event)
        elif event.type == pygame.MOUSEBUTTONUP and event.button in (4, 5):
            self.handle_mouse_wheel(event)
            
    def handle_mouse_click(self, event):
        # Tab switching
        if self.playlist_tab.collidepoint(event.pos) and self.playlist_tab.collidepoint(MOUSE_DOWN_POS):
            self.current_tab = 0
            self.loop()
        elif self.lyrics_tab.collidepoint(event.pos) and self.lyrics_tab.collidepoint(MOUSE_DOWN_POS):
            self.current_tab = 1
            self.loop()
        elif self.playlists_tab.collidepoint(event.pos) and self.playlists_tab.collidepoint(MOUSE_DOWN_POS):
            self.current_tab = 2
            self.loop()
            
        # Content area clicks
        elif (self.background.collidepoint(event.pos) and 
              not self.tab_bar.collidepoint(event.pos) and 
              -20 < event.pos[0] - MOUSE_DOWN_POS[0] < 20):
                  
            if self.current_tab == 0:  # Playlist
                self.handle_playlist_click(event)
            elif self.current_tab == 1:  # Lyrics analysis
                self.handle_lyrics_click(event)
            elif self.current_tab == 2:  # Playlists
                self.handle_playlists_click(event)
                
    def handle_playlist_click(self, event):
        item_index = (event.pos[1] + self.playlist_scroll - location_size.labal.height) // location_size.name_peritem
        if 0 <= item_index < len(player.playlist):
            # Info icon click
            if (location_size.info.x <= event.pos[0] <= location_size.info.x + location_size.info.weight and
                self.show_info_dialog):
                self.show_info_dialog = False
                self.show_song_info(player.playlist[item_index])
            # Song selection
            else:
                player.current_index = item_index
                player.replay()
                
    def show_song_info(self, song_path):
        def show_info():
            try:
                mp3 = MP3(song_path)
                tags = mp3.tags
                info = mp3.info
                
                # Get metadata
                title = tags.get('TIT2', ['NULL'])[0]
                artist = tags.get('TPE1', ['NULL'])[0]
                
                # File size formatting
                size = os.path.getsize(song_path)
                if size >= 1024 * 1024:
                    size_str = f"歌曲大小:{size/(1024 * 1024):.2f}MB\n"
                elif size >= 1024:
                    size_str = f"歌曲大小:{size/1024:.2f}KB\n"
                else:
                    size_str = f"歌曲大小:{size}Bytes\n"
                    
                # Bitrate formatting
                bitrate = getattr(info, 'bitrate', 0)
                if bitrate >= 1000000 and bitrate % 1000000 == 0:
                    bitrate_str = f"比特率:{bitrate//1000000}Mbps\n"
                elif bitrate >= 1000 and bitrate % 1000 == 0:
                    bitrate_str = f"比特率:{bitrate//1000}Kbps\n"
                else:
                    bitrate_str = f"比特率:{bitrate}bps\n"
                    
                # Show dialog
                tkinter.messagebox.showinfo(
                    "歌曲信息",
                    f"歌曲名:{title}\n" +
                    f"歌手:{artist}\n" +
                    size_str +
                    f"歌曲长度:{info.length:.2f}s\n" +
                    bitrate_str +
                    f"声道数:{getattr(info, 'channels', 'N/A')}\n" +
                    f"采样率:{getattr(info, 'sample_rate', 'N/A')}Hz"
                )
            except Exception as e:
                tkinter.messagebox.showerror("错误", f"无法读取歌曲信息: {str(e)}")
            finally:
                self.show_info_dialog = True
                
        threading.Thread(target=show_info, daemon=True).start()
        
    def handle_lyrics_click(self, event):
        line_index = ((event.pos[1] + self.lyrics_scroll - location_size.labal.height) // 
                     location_size.word_peritem - 9)
        if 0 <= line_index < len(self.lyric_items):
            player_interface.current_lyric_index = 0
            player.seek(self.lyric_items[line_index])
            
    def handle_playlists_click(self, event):
        item_index = ((event.pos[1] + self.playlists_scroll - location_size.labal.height) // 
                     location_size.word_peritem)
        if 0 <= item_index < len(self.playlist_commands):
            command = self.playlist_commands[item_index]
            
            if command is None:
                return
            elif not isinstance(command, tuple):
                command()  # Execute the function (add folder)
            else:
                # Remove folder if info icon clicked
                if (location_size.info.x <= event.pos[0] <= location_size.info.x + location_size.info.weight and
                    command[0] in player.additional_folders):
                    player.additional_folders.remove(command[0])
                else:
                    player.set_playlist(*command)
                    self.playlist_scroll = 0
                    self.playlists_scroll = 0
                    self.current_tab = 0
                    
    def handle_mouse_wheel(self, event):
        scroll_up = event.button == 4
        if self.background.collidepoint(event.pos) and not self.tab_bar.collidepoint(event.pos):
            if self.current_tab == 0:  # Playlist
                self.scroll_playlist(scroll_up)
            elif self.current_tab == 1:  # Lyrics analysis
                self.scroll_lyrics(scroll_up)
            elif self.current_tab == 2:  # Playlists
                self.scroll_playlists(scroll_up)
                
    def scroll_playlist(self, scroll_up):
        max_items = len(player.playlist)
        item_height = location_size.name_peritem
        visible_height = location_size.surface_2.height
        
        if scroll_up:
            if self.playlist_scroll > location_size.step:
                self.playlist_scroll -= location_size.step
            else:
                self.playlist_scroll = 0
        else:
            total_height = (max_items + 3) * item_height
            if total_height > visible_height + self.playlist_scroll:
                self.playlist_scroll += location_size.step
                
    def scroll_lyrics(self, scroll_up):
        if scroll_up:
            if self.lyrics_scroll > location_size.step:
                self.lyrics_scroll -= location_size.step
            else:
                self.lyrics_scroll = 0
        else:
            total_height = (self.total_lyric_lines + 3) * location_size.word_peritem
            if total_height > location_size.surface_2.height + self.lyrics_scroll:
                self.lyrics_scroll += location_size.step
                
    def scroll_playlists(self, scroll_up):
        if scroll_up:
            if self.playlists_scroll > location_size.step:
                self.playlists_scroll -= location_size.step
            else:
                self.playlists_scroll = 0
        else:
            total_items = len(self.playlist_commands)
            total_height = (total_items + 3) * location_size.word_peritem
            if total_height > location_size.surface_2.height + self.playlists_scroll:
                self.playlists_scroll += location_size.step

# 音乐播放器
class MusicPlayer:
    def __init__(self):
        self.current_index = 0
        self.music_folder = r'.\\music'
        self.current_playlist = '\\'
        self.play_start_time = 0
        self.show_dialogs = True
        self.play_mode = 0  # 0: loop all, 1: loop one, 2: random
        self.is_accompaniment = False
        self.volume = 0.5
        self.additional_folders = []
        
        self.set_playlist(self.music_folder, self.current_playlist)
        
        pygame.mixer.music.load(self.playlist[self.current_index])
        pygame.mixer.music.play(start=(4 * 60 + 30))  # Start at 4:30 for testing
        pygame.mixer.music.pause()
        pygame.mixer.music.set_endevent(music_events.MUSIC_END)
        
        mp3 = MP3(self.playlist[self.current_index])
        self.tags = mp3.tags
        self.song_info = mp3.info
        
    def set_playlist(self, folder_path, playlist_name='\\', relative=True):
        self.current_index = 0
        
        if playlist_name == '\\' or not relative:
            songs = [f'{folder_path}\\{f}' for f in os.listdir(folder_path) if f.endswith('.mp3')]
            if songs:
                self.music_folder = folder_path
                self.playlist = songs
                self.current_playlist = "\\"
                self.replay()
            else:
                if folder_path in self.additional_folders:
                    self.additional_folders.remove(folder_path)
                if self.show_dialogs:
                    self.show_dialogs = False
                    def show_warning():
                        tkinter.messagebox.showwarning('警告', f'文件夹{folder_path}中没有MP3文件')
                        self.show_dialogs = True
                    threading.Thread(target=show_warning, daemon=True).start()
        else:
            try:
                with open(f"{folder_path}/歌单/{playlist_name}", 'r', encoding='utf-8') as f:
                    self.music_folder = folder_path
                    self.current_playlist = playlist_name
                    self.playlist = [f'{self.music_folder}\\{song}' 
                                   for song in json.load(f) if song.endswith('.mp3')]
                    self.replay()
            except Exception as e:
                if self.show_dialogs:
                    self.show_dialogs = False
                    def show_error():
                        tkinter.messagebox.showerror('错误', f'无法加载歌单: {str(e)}')
                        self.show_dialogs = True
                    threading.Thread(target=show_error, daemon=True).start()
                    
    def get_position(self):
        return pygame.mixer.music.get_pos() / 1000 + self.play_start_time
        
    def increase_volume(self):
        current_vol = pygame.mixer.music.get_volume()
        if current_vol < 0.9:
            pygame.mixer.music.set_volume(current_vol + 0.1)
        else:
            pygame.mixer.music.set_volume(1.0)
            
    def decrease_volume(self):
        current_vol = pygame.mixer.music.get_volume()
        if current_vol > 0.1:
            pygame.mixer.music.set_volume(current_vol - 0.1)
        else:
            pygame.mixer.music.set_volume(0.0)
            
    def toggle_accompaniment(self):
        if self.is_accompaniment:
            self.play_start_time = self.get_position()
            self.is_accompaniment = False
            pygame.mixer.music.load(self.playlist[self.current_index])
            pygame.mixer.music.play(start=self.play_start_time)
        else:
            accompaniment_folder = f'{self.music_folder}/伴奏'
            if os.path.exists(accompaniment_folder):
                for f in os.listdir(accompaniment_folder):
                    try:
                        if (str(self.tags['TIT2'][0]) in f and '伴奏' in f and 
                            f.endswith('.mp3')):
                            pygame.mixer.music.load(f'{accompaniment_folder}/{f}')
                            self.play_start_time = self.get_position()
                            pygame.mixer.music.play(start=self.play_start_time)
                            self.is_accompaniment = True
                            break
                    except:
                        continue
        self.unpause()
        
    def change_song(self, playlist, index):
        self.playlist = playlist
        self.current_index = index
        self.unpause()
        pygame.event.post(pygame.event.Event(music_events.SONG_CHANGE))
        pygame.mixer.music.load(playlist[index])
        pygame.mixer.music.play()
        
    def change_play_mode(self):
        self.play_mode = (self.play_mode + 1) % 3  # Cycle through 0, 1, 2
        
    def previous_song(self):
        if self.play_mode in (0, 1):  # Loop modes
            if self.current_index > 0:
                self.current_index -= 1
            else:
                self.current_index = len(self.playlist) - 1
        else:  # Random mode
            self.current_index = random.randint(0, len(self.playlist) - 1)
            
        self.unpause()
        pygame.event.post(pygame.event.Event(music_events.SONG_CHANGE))
        pygame.mixer.music.load(self.playlist[self.current_index])
        pygame.mixer.music.play()
        
    def next_song(self):
        if self.play_mode in (0, 1):  # Loop modes
            if self.current_index < len(self.playlist) - 1:
                self.current_index += 1
            else:
                self.current_index = 0
        else:  # Random mode
            self.current_index = random.randint(0, len(self.playlist) - 1)
            
        self.unpause()
        pygame.event.post(pygame.event.Event(music_events.SONG_CHANGE))
        pygame.mixer.music.load(self.playlist[self.current_index])
        pygame.mixer.music.play()
        
    def seek(self, time):
        time = max(0, min(time, self.song_info.length))
        
        if self.is_accompaniment:
            accompaniment_folder = f'{self.music_folder}/伴奏'
            if os.path.exists(accompaniment_folder):
                for f in os.listdir(accompaniment_folder):
                    try:
                        if (str(self.tags['TIT2'][0]) in f and '伴奏' in f and 
                            f.endswith('.mp3')):
                            pygame.mixer.music.load(f'{accompaniment_folder}/{f}')
                            pygame.mixer.music.play(start=time)
                            break
                    except:
                        continue
        else:
            pygame.mixer.music.load(self.playlist[self.current_index])
            pygame.mixer.music.play(start=time)
            
        self.play_start_time = time
        player_interface.current_lyric_index = 0
        self.unpause()
        
    def pause(self):
        pygame.event.post(pygame.event.Event(music_events.PAUSE))
        pygame.mixer.music.pause()
        self.is_playing = False
        
    def unpause(self):
        pygame.event.post(pygame.event.Event(music_events.UNPAUSE))
        pygame.mixer.music.unpause()
        self.is_playing = True
        
    def replay(self):
        pygame.event.post(pygame.event.Event(music_events.SONG_CHANGE))
        pygame.mixer.music.load(self.playlist[self.current_index])
        pygame.mixer.music.play()
        self.unpause()
        
    def event(self, event):
        if event.type == music_events.SONG_CHANGE:
            self.play_start_time = 0
            mp3 = MP3(self.playlist[self.current_index])
            self.tags = mp3.tags
            self.song_info = mp3.info
        elif event.type == music_events.MUSIC_END:
            if self.play_mode in (0, 2):  # Loop all or random
                self.next_song()
            elif self.play_mode == 1:  # Loop one
                self.replay()

# 初始化
player = MusicPlayer()
player_interface = PlayerInterface()
lyrics_sidebar = LyricsSidebar()

BASE_TIME = time.time()
player_interface.entry()
player.replay()

# 主循环
if __name__ == "__main__":
    while True:
        pygame.draw.rect(screen, (255, 255, 255), location_size.window2.r)
        
        player_interface.loop()
        lyrics_sidebar.loop()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if tkinter.messagebox.askyesno('退出程序', '真就这样离开了吗QAQ~'):
                    pygame.quit()
                    sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                MOUSE_DOWN_POS = event.pos
                
            player.event(event)
            player_interface.event(event)
            lyrics_sidebar.event(event)
            
        pygame.display.flip()