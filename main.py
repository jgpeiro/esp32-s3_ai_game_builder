import time
import wifi
import secrets
import asyncio

import hal_utils
import api_utils
import i2s_utils
import prompt_utils
import lvgl_utils
import lvgl as lv

from tools_default import read_file_tool_desc, write_file_tool_desc, run_file_tool_desc
from tools_default import read_file_tool, write_file_tool, run_file_tool

import machine

hal_utils.init()
lvgl_utils.init()

tools_funcs = {}
tools_funcs["read_file"] = read_file_tool
tools_funcs["write_file"] = write_file_tool
tools_funcs["run_file"] = run_file_tool
tools_dicts = []
tools_dicts.append( read_file_tool_desc )
tools_dicts.append( write_file_tool_desc )
tools_dicts.append( run_file_tool_desc )

ip = wifi.connect( secrets.WIFI_SSID, secrets.WIFI_PASSWORD )
print( ip )

def init_ui():
    scr = lv.obj()
    
    chat_container = lv.obj(scr)
    chat_container.align(lv.ALIGN.TOP_MID, 0, 0)
    chat_container.set_size(240, 200)
#     chat_container.set_style_bg_color(lv.color_white(), 0)
    chat_container.set_style_border_width(1, 0)
    chat_container.set_style_border_color(lv.color_make(0xd0, 0xd0, 0xd0), 0)
    chat_container.set_style_pad_all(5, 0)
    chat_container.set_flex_flow(lv.FLEX_FLOW.COLUMN)
    chat_container.set_flex_align(lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.START, lv.FLEX_ALIGN.START)
    chat_container.set_scrollbar_mode(lv.SCROLLBAR_MODE.AUTO)
    
    status_label = lv.label(scr)
    status_label.set_size(100, 20)
    status_label.set_text("")
    status_label.set_style_text_color( lv.color_make(0xd0, 0xd0, 0xd0), 0 )
    status_label.align(lv.ALIGN.BOTTOM_LEFT, 10, -10)
    
    send_btn = lv.button(scr)
    send_btn.set_size(60, 20)
    send_btn.align(lv.ALIGN.BOTTOM_RIGHT, -10, -10)
    send_label = lv.label(send_btn)
    send_label.set_text("Rec")
    send_label.center()
    #send_btn.add_event_cb(pressed, lv.EVENT.PRESSED, None)
    send_btn.add_state( lv.STATE.DISABLED )
    
    lv.screen_load( scr )
    
    group = lv.group_create()
    group.add_obj( send_btn )
    lvgl_utils.indev_drv.set_group( group )
    return chat_container, send_btn, status_label

def remove_accents(text):
    accents_in = "áéíóúñÁÉÍÓÚÑ"
    accents_out= "aeiounAEIOUN"
    for i, o in zip(accents_in, accents_out):
        text = text.replace(i, o)
    text = text.replace("¿", "")
    text = text.replace("¡", "")
    return text

def add_message( parent, text, y=0, color=None ):
    msg = lv.label( parent )
    msg.set_text( remove_accents( text ) )
    msg.set_long_mode(lv.label.LONG.WRAP)
    msg.set_width(225)
    
    if( color ):
        msg.set_style_text_color( color, 0 )
    
    msg.set_style_pad_all(5, 0)
    msg.set_style_radius(5, 0)
    msg.set_style_border_width(1, 0)
    msg.set_style_border_color(lv.color_make(0xd0, 0xd0, 0xd0), 0)
    
    msg.align(lv.ALIGN.TOP_LEFT, 5, y)
    y += msg.get_height() + 10
    
    parent.scroll_to_y( lv.COORD.MAX , lv.ANIM.OFF )
    
    return y

async def handle_joystick( parent ):
    while( True ):
        if not hal_utils.joy_up.value():
            parent.scroll_to_y(parent.get_scroll_y() - 10, lv.ANIM.OFF )
        elif not hal_utils.joy_down.value():
            parent.scroll_to_y(parent.get_scroll_y() + 10, lv.ANIM.OFF )
        await asyncio.sleep(0.1)

def is_a_pressed():
    return not hal_utils.btn_a.value()

def is_d_pressed():
    return not hal_utils.btn_d.value()


async def main():
    chat_container, send_btn, status_label = init_ui()
    task1 = asyncio.create_task( lvgl_utils.task_lvgl() )
    task2 = asyncio.create_task( handle_joystick(chat_container) )
    status_label.set_text( "Ready" )
    
    send_btn.add_state( lv.STATE.DISABLED )
    await asyncio.sleep_ms(10)
    
    msg_y = 5
    messages = []
    
    text = "Hola"
    while( True ):
        messages.append( { "role": "user", "content": text } )
        msg_y = add_message( chat_container, text, msg_y, lv.color_make(255, 0, 153) )
        await asyncio.sleep_ms(10)
        
        status_label.set_text( "Thinking..." )
        response = await api_utils.llm( secrets.ANTHROPIC_KEY.decode(), messages=messages, tools=tools_dicts, system_prompt=prompt_utils.system_prompt, max_tokens=8192 )
        messages.append( { "role": "assistant", "content": response["content"] } )
        status_label.set_text( "Done..." )
        
        while response["stop_reason"] == "tool_use":
            status_label.set_text( "Thinking..." )
            for content in response["content"]:
                if content["type"] == "text":
                    print( f"Thinking:", content["text"] )
                    msg_y = add_message( chat_container, "Thinking:\n" + content["text"][0:40] + "...", msg_y, lv.palette_main(lv.PALETTE.YELLOW) )
                    await asyncio.sleep_ms(10)
            
            status_label.set_text( "Working..." )
            tool_results = []
            for content in response["content"]:
                if content["type"] == "tool_use":
                    msg_y = add_message( chat_container, "Tool call:\n" + content["name"] + " with args " + str( content["input"] )[0:40] + "..." , msg_y, lv.palette_main(lv.PALETTE.ORANGE) )
                    await asyncio.sleep_ms(10)
                    if content["name"] in tools_funcs:
                        if( content["name"] == "run_file" ):
                            task1.cancel()
                            task2.cancel()
                            with open( "game_logs.txt", "w" ) as fl:
                                pass
                        result = tools_funcs[content["name"]](**content["input"])
                        if( content["name"] == "run_file" ):
                            with open( "game_logs.txt", "w" ) as fl:
                                fl.write( result )
                            machine.soft_reset()
                            #hal_utils.init()
                            #task1 = asyncio.create_task( lvgl_utils.task_lvgl() )
                            #task2 = asyncio.create_task( handle_joystick(chat_container) )
                        msg_y = add_message( chat_container, "Tool result:\n" + str( result )[0:40] + "..." , msg_y, lv.palette_main(lv.PALETTE.ORANGE) )
                        await asyncio.sleep_ms(10)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content["id"],
                            "content": str(result)
                        })
                    else:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content["id"],
                            "content": f"Error: Tool '{content['name']}' not found."
                        })
            
            messages.append({"role": "user", "content": tool_results})
            status_label.set_text( "Thinking..." )
            response = await api_utils.llm( secrets.ANTHROPIC_KEY.decode(), messages=messages, tools=tools_dicts, system_prompt=prompt_utils.system_prompt, max_tokens=8192 )
            status_label.set_text( "Done..." )
            messages.append({"role": "assistant", "content": response["content"]})
        
        assert len(response["content"]) == 1
        msg_y = add_message( chat_container, response["content"][0]["text"], msg_y, lv.palette_main(lv.PALETTE.BLUE) )
        print("LLM: ", response["content"][0]["text"] )
        await asyncio.sleep_ms(10)
        status_label.set_text( "Playing..." )
        await i2s_utils.play( secrets.OPENAI_KEY, response["content"][0]["text"], is_d_pressed )
        status_label.set_text( "Done..." )
        
        send_btn.remove_state( lv.STATE.DISABLED )
        send_btn.set_state( lv.STATE.FOCUSED, 0 )
        while( not is_a_pressed() ):
            await asyncio.sleep_ms(10)
        
        status_label.set_text( "Record..." )
        audio = await i2s_utils.record( is_a_pressed, 10 )
        send_btn.add_state( lv.STATE.DISABLED )
        
        status_label.set_text( "Decode..." )
        text = await api_utils.speech_to_text( secrets.OPENAI_KEY, audio )
        #text = input( "User: " )
        print( "User", text )

        
asyncio.run(main())

print("done")