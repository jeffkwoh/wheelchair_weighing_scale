# Wheelchair Weighing Scale

## Motivation

A child's weight is an important indicator of their health.
Especially moreso for children suffering from disabilities, their weight is important in determining the dosage of medication and monitoring their growth.

Taking the weight of those who are wheelchair bound can be extremely tedious for both the patient and the healthcare professional. The child must be hoisted off the wheelchair carefully, have the wheelchair's weight taken, in order to derive his weight.

This process introduces 3 complications:
1. The child may be injured if not hoisted with care
2. Being hoisted off is allegedly an unpleasant experience, creating a negative association with having one's weight taken
3. The healthcare professional may be injured if he cannot handle the child's weight

As such we aim to **create a weighing scale which gives a more positive experience to the child**.

***This is achieved by building a weighing scale that is able to measure the child's weight while he's on the wheelchair after one calibration***

## Components

The system comprises of a Raspberry Pi, which acts as a central processor. It is connected to the following:

1. HX711 (provides weight readings via GPIO)
    - Load cells
2. Arduino (provides NFC readings via USB serial)
    - NFC Tag Reader
3. LCD (output via GPIO)

## Features to develop

Please see https://github.com/unsatisfiedpopcorn/wheelchair_weighing_scale/projects/1 for features to develop
