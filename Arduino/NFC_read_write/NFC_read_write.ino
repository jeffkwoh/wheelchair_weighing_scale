#include <PN532.h>
#include <PN532_HSU.h>
#include <NfcAdapter.h>

// TODO: Standardise STATE and PREFIX to be the same symbol
#define REGISTRATION_STATE '!'
#define WHEELCHAIR_WEIGHT_PREFIX " :"
#define WHEELCHAIR_WEIGHT_SYMBOL ':'
#define UPDATE_WEIGHT_STATE '@'
#define PATIENT_WEIGHT_PREFIX " @"
#define LIBRARY_TEXT_RECORD_PREFIX "\02en"

PN532_HSU pn532hsu(Serial1);
//PN532 nfc(pn532hsu);
NfcAdapter nfc = NfcAdapter(pn532hsu);  // Indicates the Shield you are using

void setup(void) {
  Serial.begin(9600);
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

    if (nfc.tagPresent()) {
      NfcTag tag = nfc.read();
      NdefMessage message = NdefMessage();

      message.addTextRecord(WHEELCHAIR_WEIGHT_PREFIX + receivedStr); // Text Message you want to Record

      // If tag already has a message, extract all the previous records
      // EXCLUDING the wheelchairWeight record and append them to the new message
      // TODO: Extract method
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

          // if current record has been detected ot be a wheelchair record, 
          // skip the rest of the instructions
          // and go to the next iterable
          if (isWheelChairWeightRecord) {
            continue;
          }

          // Replace unwanted prefix that is automatically encoded by 
          // message::addTextRecord
          payloadAsString.replace(LIBRARY_TEXT_RECORD_PREFIX, "");
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
  } else if (receivedChar == UPDATE_WEIGHT_STATE) { // Expected input @patient_weight@
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
      
      // Only attempts to write if NFC tag has less than 2 records
      // Currently experiencing a problem when the 3rd block is written into
      boolean success = message.getRecordCount() > 2 ? false : nfc.write(message);
      if (success) {
        Serial.println("NFC tag successfully written!"); // if it works you will see this message 
      } else {
        Serial.println("Write failed"); // If the the rewrite failed you will see this message
      }
    }
  }

}
/**
* Converts an NdefMessage into its String representation for outputting via serial
*
*/
void extractMessage(NdefMessage message, String &target) {
  target = "";
  // If you have more than 1 Message then it will cycle through them
  int recordCount = message.getRecordCount();
  for (int i = 0; i < recordCount; i++) {
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

    payloadAsString.replace(LIBRARY_TEXT_RECORD_PREFIX, "");

    target += payloadAsString; 
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
    }
  }
  delay(1000); // Variable delay to tweak and find the Magic Number
}
