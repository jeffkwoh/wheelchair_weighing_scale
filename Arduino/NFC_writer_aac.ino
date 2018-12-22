// Write info to NFC tag

#include <PN532_HSU.h>
#include <PN532.h>
#include <NfcAdapter.h>

PN532_HSU pn532hsu(Serial1);
//PN532 nfc(pn532hsu);
NfcAdapter nfc = NfcAdapter(pn532hsu);  // Indicates the Shield you are using

void setup() {
    Serial.begin(9600);
    Serial.println("NFC Tag Writer"); // Serial Monitor Message
    nfc.begin();
}

void loop() {
    Serial.println("\nPlace an NFC Tag that you want to Record these Messages on!"); // Command for the Serial Monitor
    if (nfc.tagPresent()) {
        NdefMessage message = NdefMessage();
        message.addTextRecord("60.23,45.1"); // Text Message you want to Record
        boolean success = nfc.write(message);
        if (success) {
            Serial.println("NFC tag successfully written!"); // if it works you will see this message 
        } else {
            Serial.println("Write failed"); // If the the rewrite failed you will see this message
        }
    }
    delay(10000);
}
