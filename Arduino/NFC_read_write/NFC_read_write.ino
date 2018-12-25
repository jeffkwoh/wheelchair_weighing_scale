#include <PN532.h>
#include <PN532_HSU.h>
#include <NfcAdapter.h>

#define REGISTRATION_STATE '!'
#define WHEELCHAIR_WEIGHT_PREFIX " :"

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
    Serial.print(receivedStr);
    // TODO: change ONLY the wheelchair weight, preserving everything else.
     if (nfc.tagPresent()) {
        NdefMessage message = NdefMessage();
        message.addTextRecord(WHEELCHAIR_WEIGHT_PREFIX + receivedStr); // Text Message you want to Record
        boolean success = nfc.write(message);
        if (success) {
            Serial.println("NFC tag successfully written!"); // if it works you will see this message 
        } else {
            Serial.println("Write failed"); // If the the rewrite failed you will see this message
        }
    }
  }
 
}

void loop(void) {
//  Serial.println("\nScan your NFC tag on the NFC Shield\n");  // Command so that you an others will know what to do 

  if (nfc.tagPresent())
  {
    NfcTag tag = nfc.read();
//    Serial.println(tag.getTagType());
//    Serial.print("UID: ");
//    Serial.println(tag.getUidString()); // Retrieves the Unique Identification from your tag

    if (tag.hasNdefMessage()) // If your tag has a message
    {

      NdefMessage message = tag.getNdefMessage();
//      Serial.print("\nThis Message in this Tag is ");
//      Serial.print(message.getRecordCount());
////      Serial.print(" NFC Tag Record");
//      if (message.getRecordCount() != 1) { 
//        Serial.print("s");
//      }
//      Serial.println(".");

      // If you have more than 1 Message then it will cycle through them
      int recordCount = message.getRecordCount();
      for (int i = 0; i < recordCount; i++)
      {
//        Serial.print("\nNDEF Record ");Serial.println(i+1);
        NdefRecord record = message.getRecord(i);

        int payloadLength = record.getPayloadLength();
        byte payload[payloadLength];
        record.getPayload(payload);


        String payloadAsString = ""; // Processes the message as a string vs as a HEX value
        for (int c = 0; c < payloadLength; c++) {
          payloadAsString += (char)payload[c];
        }
//        Serial.print("  Information (as String): ");
        Serial.print(payloadAsString);

        
        String uid = record.getId();
        if (uid != "") {
//          Serial.print("  ID: ");Serial.println(uid); // Prints the Unique Identification of the NFC Tag
        }
      }
      Serial.println("");
    }
  }
  delay(5000);
}
