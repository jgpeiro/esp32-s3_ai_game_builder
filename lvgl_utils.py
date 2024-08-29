import time
import lvgl as lv
import hal_utils
import asyncio



# Display driver
def disp_drv_cb( disp_drv, area, color ):
    global lcd
    x, y = area.x1, area.y1
    w, h = area.x2 - area.x1 + 1, area.y2 - area.y1 + 1
    size = w*h
    buf = color.__dereference__( size*2 )
    lv.draw_sw_rgb565_swap( buf, size )
    hal_utils.lcd.write_bmp( buf, x, y, w, h )
    disp_drv.flush_ready()

# Input driver
up_bck, down_bck, a_bck = 0, 0, 0
def indev_drv_cb( indev_drv, data ):
    global joy_up, joy_down, btn_a
    global up_bck, down_bck, a_bck
    
    up, down, a = not hal_utils.joy_up.value(), not hal_utils.joy_down.value(), not hal_utils.btn_a.value()
    
    if( up and not up_bck ):
        data.enc_diff =-1
    elif( down and not down_bck ):
        data.enc_diff = 1
    else:
        data.enc_diff = 0

    if( a ):
        data.state = lv.INDEV_STATE.PRESSED
    else:
        data.state = lv.INDEV_STATE.RELEASED
    
    up_bck, down_bck, a_bck = up, down, a
    return True

indev_drv = None
def init():
    global indev_drv
    
    # LVGL initialization
    lv.init()

    disp_drv_buf = bytearray( hal_utils.LCD_WIDTH*hal_utils.LCD_HEIGHT*2 )
    hal_utils.lcd.write_bmp( disp_drv_buf )

    disp_drv = lv.display_create( hal_utils.LCD_WIDTH, hal_utils.LCD_HEIGHT )
    disp_drv.set_flush_cb( disp_drv_cb )
    disp_drv.set_color_format(lv.COLOR_FORMAT.RGB565)
    disp_drv.set_buffers( disp_drv_buf, None, len(disp_drv_buf), lv.DISPLAY_RENDER_MODE.PARTIAL )

    indev_drv = lv.indev_create()
    indev_drv.set_read_cb( indev_drv_cb )
    indev_drv.set_type( lv.INDEV_TYPE.ENCODER )

async def task_lvgl( period=50 ):
    t0 = time.ticks_ms()
    while True:
        lv.task_handler()
        t1 = t0
        t0 = time.ticks_ms()        
        dt = time.ticks_diff(t0, t1)
        if dt < period:
            await asyncio.sleep_ms(period - dt)
            lv.tick_inc(period)
        else:
            await asyncio.sleep_ms(1)
            lv.tick_inc(dt+1)