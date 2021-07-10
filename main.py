gc.collect()
async def main(client):
    gc.collect()
    await client.connect()
    while True:
        await runTasks(oled)

async def runTasks(led):
    read_ok = await read_serial_values(uart_esp32)
    if read_ok:
        Va_rms, Vb_rms, Vc_rms, Va_THD, Vb_THD, Vc_THD = calcRMSTHD()
        print(Va_rms, Vb_rms, Vc_rms)
        drawScreen(led, Va_rms, Vb_rms, Vc_rms, Va_THD, Vb_THD, Vc_THD)
        await publishRMS(client, [Va_rms, Vb_rms, Vc_rms])
        await publishTHD(client, [Va_THD, Vb_THD, Vc_THD])
        drawStatus(led)


@micropython.native
def calcRMSTHD():
    Va_np = calibra(Va, offset_A, max_A)
    Vb_np = calibra(Vb, offset_B, max_B)
    Vc_np = calibra(Vc, offset_C, max_C)
    Va_rms = rms(Va_np)
    Vb_rms = rms(Vb_np)
    Vc_rms = rms(Vc_np)
    Va_THD = THD(Va_np)
    Vb_THD = THD(Vb_np) 
    Vc_THD = THD(Vc_np)
    return Va_rms, Vb_rms, Vc_rms, Va_THD, Vb_THD, Vc_THD
    
@micropython.native
def drawStatus(led):
    global px_s
    px_s = (px_s +1 ) % oled_width
    led.text('.',px_s,40)
    led.show()

async def publishSag(client, array):
    msg_mqtt = bytearray()
    for i in range( len(array) ):
        msg_mqtt.append(array[i] & 0xff)
        msg_mqtt.append(array[i] >> 8)
    gc.collect()
    await client.publish(b'saguard/'+client_id+b'/sag', msg_mqtt)

async def publishRMS(client, array):
    msg_mqtt = bytearray()
    msg_mqtt.append(int(array[0]*100) & 0xff)
    msg_mqtt.append(int(array[0]*100) >> 8)
    msg_mqtt.append(int(array[1]*100) & 0xff)
    msg_mqtt.append(int(array[1]*100) >> 8)
    msg_mqtt.append(int(array[2]*100) & 0xff)
    msg_mqtt.append(int(array[2]*100) >> 8)
    gc.collect()
    await client.publish(b'saguard/'+client_id+b'/rms', msg_mqtt)

async def publishTHD(client, array):
    msg_mqtt = bytearray()
    msg_mqtt.append(int(array[0]*100) & 0xff)
    msg_mqtt.append(int(array[0]*100) >> 8)
    msg_mqtt.append(int(array[1]*100) & 0xff)
    msg_mqtt.append(int(array[1]*100) >> 8)
    msg_mqtt.append(int(array[2]*100) & 0xff)
    msg_mqtt.append(int(array[2]*100) >> 8)
    gc.collect()
    await client.publish(b'saguard/'+client_id+b'/thd', msg_mqtt)

@micropython.native
def drawScreen(led, Va_rms, Vb_rms, Vc_rms, Va_THD, Vb_THD, Vc_THD):
    _text = led.text
    str_Va = '{0:.1f}V'.format(Va_rms)
    str_Vb = '{0:.1f}V'.format(Vb_rms)
    str_Vc = '{0:.1f}V'.format(Vc_rms)
    str_THDa = '{0:.1f}%'.format(Va_THD)
    str_THDb = '{0:.1f}%'.format(Vb_THD)
    str_THDc = '{0:.1f}%'.format(Vc_THD)
    led.fill(0)
    _text("RMS", 24, 1)
    _text("Va", 0, 10)
    _text(str_Va, 24, 10)
    _text("Vb", 0, 20)
    _text(str_Vb, 24, 20)
    _text("Vc", 0, 30)
    _text(str_Vc, 24, 30)

    _text("THD", 80, 1)
    _text(str_THDa, 80, 10)
    _text(str_THDb, 80, 20)
    _text(str_THDc, 80, 30)
    # Atualiza o display
    led.show()

@micropython.native
def flush_uart(uart):
    print('Flush')
    while uart.any() > 0:
        uart.read( uart.any() )

async def read_serial_values(uart):
    """ Read values from UART """    
    uany = uart.any
    read = uart.read
    while (uany() < 4 ):
        pass
    
    data_type = ord( read(1) )
    # print(data_type)
    if data_type == 242:
        global Va, Vb, Vc
        gc.collect()

        n_phase = read(1)
        ar_sz_b = read(2) # Size array
        ar_sz = ar_sz_b[0] | ar_sz_b[1] << 8
        del ar_sz_b
        # print(ar_sz)
        if ar_sz != 1024:
            flush_uart(uart)
            return False
        
        # Va = [0]*_sr
        # Vb = [0]*_sr
        # Vc = [0]*_sr
        if ord(n_phase) == 1:
            while (uany() < ar_sz):
                pass
            for i in range(sr) :
                message = uart.read(2)
                Va[i] = (message[0] | message[1] << 8)
        else:
            # print("Passou no primeiro")
            for i in range(sr):
                message = read(2)
                Va[i] = (message[0] | message[1] << 8)
            # print("Passou no segundo")
            for i in range(sr):
                message = read(2)
                Vb[i] = (message[0] | message[1] << 8)
            # print("Passou no terceiro")
            for i in range(sr):
                message = read(2)
                Vc[i] = (message[0] | message[1] << 8)
        # print(Va[0:10])
        # print(Vb[0:10])
        # print(Vc[0:10])
        last_byte = ord( read(1) )
        # print(last_byte)
        if last_byte == 245:            
            # print("Recebeu byte final")
            return True
        else:
            return False
        
    elif data_type == 243:
        gc.collect()
        global Vsag
        ar_sz_bytes = read(2)
        ar_sz = ar_sz_byte[0] | ar_sz_byte[1] << 8
        del ar_sz_bytes
        # Vsag = [0]*_sr
        for i in range( ar_sz ) :
            message = read(2)
            Vsag[i] = (message[0] | message[1] << 8) 
        last_byte = ord( read(1) )
        if last_byte == 245: # Complete message received and on
            uart.write(bytes([245]))
            gc.collect()
            await publishSag(client, Vsag[:ar_sz])
            print(b'Sag')
            oled.text(b'Sag', 0, 55)
            oled.show()
        return False
    else:
        # Just flush
        flush_uart(uart)

@micropython.native
def calibra(array, offset, max):
    return ( np.array( array ) - offset ) * 179.61 / max

@micropython.native
def rms(array):
    return np.sqrt(np.mean(array ** 2))

@micropython.native
def THD(array):
    """Calculate the THD"""
    # global Y
    Y = None
    # R = None
    # I = None
    # print('THD RAM free {} alloc {}'.format(gc.mem_free(), gc.mem_alloc()))
    # R, I = np.fft.fft(array)
    Y = spy.signal.spectrogram(array)
    # Vfun = 2*np.sqrt( R[20]**2 + I[20]**2 )/sr
    Vfun = 2*Y[20]/sr
    # print('THD RAM free {} alloc {}'.format(gc.mem_free(), gc.mem_alloc()))
    h_max = 25
    sum_abs = 0
    # for i_h in np.arange(40,20*(h_max+1),20):
    #     sum_abs += ( np.sqrt( R[i_h]**2 + I[i_h]**2 ) /sr)*2

    # Y = spy.signal.spectrogram(array)
    # gc.collect()
    # # Fundamental 60Hz
    # Vfun = 2*Y[20]/sr
    
    # # Sum all the amplitudes 
    h_max = 25 # Max harmonic order
    for i_h in np.arange(40,20*(h_max+1),20):
        sum_abs += (Y[i_h]/sr)*2
    del Y
    # gc.collect()
    return 100 * np.sqrt( sum_abs ) / Vfun

# def callback(topic, msg, retained):
#     print(topic, msg, retained)

async def conn_han(client):
    #await client.subscribe('foo_topic', 1)
    await client.subscribe(topic_sub, 0)

# Start flow here
gc.collect()
# config['subs_cb'] = callback
config['connect_coro'] = conn_han
config['server'] = SERVER
MQTTClient.DEBUG = True  # Optional: print diagnostic messages

if __name__ == '__main__':
    # Show first infos at screen
    gc.collect()
    oled.invert(0) # Erase all
    oled.fill(0) # Clear screen
    oled.contrast(255) # Maximum contrast

    # Faz uma introdução (não é necessária)
    # oled.text("Sincronizador", 10, 15)
    oled.text(b'IoT SaGuard v1.0', 0, 10)
    # oled.text("v1.0", 38, 30)
    oled.text(b'Thales Maia', 18, 32)
    oled.text(b'thalesmaiaufmg@', 3, 50)
    oled.text(b'gmail.com', 45, 56)
    oled.show()
    gc.collect()

    sleep_ms(2000)
    oled.fill(0) # Limpa a tela
    oled.text(b'IoT SaGuard v1.0', 0, 10)
    oled.text(b'Connecting Wifi', 0, 20)
    oled.text(config['ssid'], 0, 30)
    oled.show()
    gc.collect() # Jus to be sure

    client = MQTTClient(config, oled)
    gc.collect()

    try:
        asyncio.run(main(client))
    except KeyboardInterrupt:
        print('Interrupted')