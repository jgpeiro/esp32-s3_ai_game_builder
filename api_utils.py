import aiohttp
import json
import io

async def llm(api_key, messages, max_tokens=8192, temp=0, system_prompt=None, tools=None):
    model = "claude-3-5-sonnet-20240620"
    
    url = "https://api.anthropic.com/v1/messages"
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "anthropic-beta": "max-tokens-3-5-sonnet-2024-07-15"
    }
    
    data = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temp,
        "messages": messages
    }
    
    if system_prompt:
        data["system"] = system_prompt

    if tools:
        data["tools"] = tools
        data["tool_choice"] = {"type": "auto"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=json.dumps(data)) as response:
            if response.status == 200:
                #print("Request successful!")
                return await response.json()
            else:
                print(f"Error: status_code = {response.status}")
                print(f"Response content: {await response.text()}")
                return None


async def text_to_speech( api_key, text, acallback=None ):
    url = "https://api.openai.com/v1/audio/speech"

    headers = {
        "Host": "api.openai.com",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "Connection": "close"
    }

    payload = {
        "model": "tts-1",
        "input": text,
        "voice": "alloy",
        "language": "Spanish",
        "response_format": "wav"
    }

    data = json.dumps(payload)

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=data) as response:
            if response.status == 200:
                #print("Request successful!")
                if( acallback ):
                    await acallback( response )
                else:
                    return await response.read()
            else:
                print(f"Error: status_code = {response.status}")
                print(f"Response content: {await response.text()}")
                return None

class FormData:
    def __init__(self):
        self.boundary = "112233445566778899" # uuid.uuid4().hex
        self.content_type = f'multipart/form-data; boundary={self.boundary}'
        self.fields = []

    def add_field(self, name, value, filename=None, content_type=None):
        self.fields.append((name, value, filename, content_type))
    
    def encode(self):
        buf = b""
        for name, value, filename, content_type in self.fields:
            buf += f'--{self.boundary}\r\n'.encode()
            if filename:
                buf += f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
                if content_type:
                    buf += f'Content-Type: {content_type}\r\n'.encode()
            else:
                buf += f'Content-Disposition: form-data; name="{name}"\r\n'.encode()
            buf += b'\r\n'
            
            if isinstance(value, io.BytesIO):
                value.seek(0)
                buf += value.read()
            else:
                buf += str(value).encode()
            
            buf += b'\r\n'
        buf += f'--{self.boundary}--\r\n'.encode()
        return buf


async def speech_to_text(api_key, bytes_io):
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    form_data = FormData()
    form_data.add_field('file', bytes_io, filename='recording.wav', content_type='audio/wav')
    form_data.add_field('model', 'whisper-1')
    
    headers['Content-Type'] = form_data.content_type

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, data=form_data) as response:
            if response.status == 200:
                #print("Request successful!")
                result = await response.json()
                return result.get('text', '')
            else:
                error_text = await response.text()
                raise Exception(f"Error: {response.status}. {error_text}")


#  deprecated. Use speech_to_text instead.
async def atranscribe( api_key, bytes_io ):
    import asyncio
    import tls
    import socket

    fl_name = "recording.wav"
    url = "https://api.openai.com/v1/audio/transcriptions"
    proto, dummy, host, path = url.split("/", 3)
    port = 443

    length = len(bytes_io.getvalue()) + 220
    length += len(fl_name)

    ai = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
    ai = ai[0]

    ssl_context = tls.SSLContext(tls.PROTOCOL_TLS_CLIENT)
    ssl_context.verify_mode = tls.CERT_NONE

    request = (
        f'POST /{path} HTTP/1.0\r\n' +
        'Host: api.openai.com\r\n' +
        'Content-Type: multipart/form-data; boundary=----1234567812345678\r\n' +
        'Connection: close\r\n' +
        f'Authorization: Bearer {api_key}\r\n' +
        f'Content-Length: {length}\r\n' +
        '\r\n' +
        '------1234567812345678\r\n' +
        f'Content-Disposition: form-data; name="file"; filename="{fl_name}"\r\n' +
        'Content-Type: audio/wav\r\n' +
        '\r\n'
    ).encode()

    footer = (
        '\r\n' +
        '------1234567812345678\r\n' +
        'Content-Disposition: form-data; name="model"\r\n' +
        '\r\n' +
        'whisper-1\r\n' +
        '------1234567812345678--\r\n' +
        '\r\n'
    ).encode()
    
    reader, writer = await asyncio.open_connection(
        host, port, ssl=ssl_context
    )
    await writer.awrite(request)
    
    bytes_io.seek(0)
    chunk = bytes_io.read(1024)
    while chunk:
        await writer.awrite(chunk)
        chunk = bytes_io.read(1024)

    await writer.awrite(footer)
    
    resp = b""
    buf = await reader.read(1024)
    while( buf ):
        resp += buf
        buf = await reader.read(1024)
    
    writer.close()
    await writer.wait_closed()
    
    return resp.split(b'"text": "')[1][:-3]
