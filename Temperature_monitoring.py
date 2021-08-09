import conf, json, time, math, statistics
# The math and statistics libraries will be required for calculating the Z-score and the threshold boundaries

from boltiot import Sms, Bolt
from conf import send_telegram_message  # importing our telegram function from conf


def compute_bounds(history_data, frame_size, factor):
    if len(history_data) < frame_size:
        return None
    if len(history_data) > frame_size:
        del history_data[0:len(history_data) - frame_size]
    Mn = statistics.mean(history_data)

    # calculating the Variance of the data points
    Variance = 0
    for data in history_data:
        Variance += math.pow((data - Mn), 2)

    # Calculating Z score for thresholds
    Zn = factor * math.sqrt(Variance / frame_size)
    High_bound = history_data[frame_size - 1] + Zn
    Low_bound = history_data[frame_size - 1] - Zn
    return [High_bound, Low_bound]


# Initializing Bolt and Sms for collecting data, storing in list and sending sms
mybolt = Bolt(conf.API_KEY, conf.DEVICE_ID)
sms = Sms(conf.SSID, conf.AUTH_TOKEN, conf.TO_NUMBER, conf.FROM_NUMBER)
history_data = []

# code for anomaly detection
while True:
    response = mybolt.analogRead('A0')
    data = json.loads(response)
    if data['success'] != 1:
        print("There was an error while retriving the data.")
        print("This is the error:" + data['value'])
        time.sleep(10)
        continue

    print("This is the value " + data['value'])
    sensor_value = 0
    try:
        sensor_value = int(data['value'])
    except e:
        print("There was an error while parsing the response: ", e)
        continue

    bound = compute_bounds(history_data, conf.FRAME_SIZE, conf.MUL_FACTOR)
    if not bound:
        required_data_count = conf.FRAME_SIZE - len(history_data)
        print("Not enough data to compute Z-score. Need ", required_data_count, " more data points")
        history_data.append(int(data['value']))
        time.sleep(10)
        continue
    try:
        if sensor_value > bound[0]:
            time.sleep(60)
            mybolt.digitalWrite('0', 'HIGH')
            print("Temperature of Fridge increased suddenly.Sending an SMS .")
            temp = sensor_value / 10.24
            response = sms.send_sms(
                "Alert,Fridge door is open.\nTemperature is beyond threshold!!!\nThe current temp val is" + " " + str(
                    temp))
            message = "Alert! Fridge door is open. Go and close it." + \
                      ". The current value is " + " " + str(temp)
            conf.send_telegram_message(message)
            mybolt.digitalWrite('0', 'LOW')
            print("This is the response ", response)
        history_data.append(sensor_value);
    except Exception as e:
        print("Error", e)
    time.sleep(10)