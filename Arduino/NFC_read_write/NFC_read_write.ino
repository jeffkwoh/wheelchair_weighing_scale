#include <PN532.h>
#include <PN532_HSU.h>
#include <NfcAdapter.h>

// TODO: Standardise STATE and PREFIX to be the same symbol
#define REGISTRATION_STATE '!'
#define WHEELCHAIR_WEIGHT_PREFIX " :"
#define WHEELCHAIR_WEIGHT_SYMBOL ':'
#define UPDATE_WEIGHT_STATE '@'
#define PATIENT_WEIGHT_PREFIX " @"

PN532_HSU pn532hsu(Serial1);
//PN532 nfc(pn532hsu);
NfcAdapter nfc = NfcAdapter(pn532hsu);  // Indicates the Shield you are using

void setup(void) {
    Serial.begin(9600);
    //  Serial.println("NFC TAG READER"); // Header used when using the serial monitor
    nfc.begin();
}

void serialEvent() {
    int incomingByte = 0;
    if (Serial.available()) {
        incomingByte = Serial.read();
    }

    if (incomingByte <= 0) {
        return;
    }

    char receivedChar = char(incomingByte);
    String receivedStr;

    // REGISTRATION expects input of this format !wheelchair_weight!
    if (receivedChar == REGISTRATION_STATE) {
        receivedStr = Serial.readStringUntil(REGISTRATION_STATE);
        receivedStr.replace("en", "");
        
        // TODO: change ONLY the wheelchair weight, preserving everything else.
        if (nfc.tagPresent()) {
            NfcTag tag = nfc.read();
            NdefMessage message = NdefMessage();

            message.addTextRecord(WHEELCHAIR_WEIGHT_PREFIX + receivedStr); // Text Message you want to Record
            
            if (tag.hasNdefMessage()) {
                NdefMessage originalMessage = tag.getNdefMessage();
            
                int recordCount = originalMessage.getRecordCount();
                for (int i = 0; i < recordCount; i++) {
                    NdefRecord record = originalMessage.getRecord(i);
            
                    int payloadLength = record.getPayloadLength();
                    byte payload[payloadLength];
                    record.getPayload(payload);

                    boolean isWheelChairWeightRecord = false;
                    String payloadAsString = ""; // Processes the message as a string vs as a HEX value
                    for (int c = 0; c < payloadLength; c++) {
                        payloadAsString += (char)payload[c];
                        // current record contains a wheelchair_weight, so it would not be added to the new message
                        if ((char)payload[c] == WHEELCHAIR_WEIGHT_SYMBOL) {
                            isWheelChairWeightRecord = true;
                            break;
                        }
                    }

                    if (isWheelChairWeightRecord) {
                        continue;
                    }
                    payloadAsString.replace("\02en", "");
                    Serial.println("RAW" + payloadAsString);
                    message.addTextRecord(payloadAsString);
                }
            } 
            
            boolean success = nfc.write(message);
            if (success) {
                Serial.println("NFC tag successfully written!"); // if it works you will see this message 
            } else {
                Serial.println("Write failed"); // If the the rewrite failed you will see this message
            }
        }
    } else if (receivedChar == UPDATE_WEIGHT_STATE) {
        receivedStr = Serial.readStringUntil(UPDATE_WEIGHT_STATE);
        if (nfc.tagPresent()) {
            NfcTag tag = nfc.read();

            NdefMessage message = NdefMessage();
            if (tag.hasNdefMessage()) {
                message = tag.getNdefMessage();
            } else {
                message = NdefMessage();
            }

            message.addTextRecord(PATIENT_WEIGHT_PREFIX + receivedStr);

            boolean success = message.getRecordCount() > 3 ? false : nfc.write(message);
            if (success) {
                Serial.println("NFC tag successfully written!"); // if it works you will see this message 
            } else {
                Serial.println("Write failed"); // If the the rewrite failed you will see this message
            }
        }
    }

}

void extractMessage(NdefMessage message, String &target) {
    target = "";
    // If you have more than 1 Message then it will cycle through them
    int recordCount = message.getRecordCount();
    for (int i = 0; i < recordCount; i++)
    {
        NdefRecord record = message.getRecord(i);

        int payloadLength = record.getPayloadLength();
        byte payload[payloadLength];
        record.getPayload(payload);

        String payloadAsString = ""; // Processes the message as a string vs as a HEX value
        for (int c = 0; c < payloadLength; c++) {
            byte b = payload[c];
            // Sanity check, ACSII only
            if (b < 128 && b >= 0) {
                payloadAsString += (char)payload[c]; 
            }          
        }

        payloadAsString.replace("\02en", "");

        target += payloadAsString; 
    }

}

/**
 * Precondition: message has one weight record
 */
void replaceWeight(NdefMessage &message,  int weight) {
    String weightStr = String(weight);
    int recordCount = message.getRecordCount();
    for (int i = 0; i < recordCount; i++) {
        NdefRecord record = message.getRecord(i);

        int payloadLength = record.getPayloadLength();
        byte payload[payloadLength];
        record.getPayload(payload);

        String payloadAsString = ""; // Processes the message as a string vs as a HEX value
        for (int c = 0; c < payloadLength; c++) {
            // current record contains a wheelchair_weight, so it would not be oi
            if ((char)payload[c] == WHEELCHAIR_WEIGHT_SYMBOL) {

            }
        }


    }
}


void loop(void) {

    if (nfc.tagPresent())
    {

        NfcTag tag = nfc.read();

        if (tag.hasNdefMessage()) // If your tag has a message
        {

            NdefMessage message = tag.getNdefMessage();
            
            String toPrint;
            extractMessage(message, toPrint);
            Serial.println(toPrint);
            Serial.println(message.getRecordCount());
        }
    }
    delay(2000);
}
