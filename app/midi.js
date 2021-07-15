
var listeners = {}
var connected = [];

function InitMidiListeners(triggerNoteOn, triggerNoteOff) {
  listeners.triggerNoteOn = triggerNoteOn;
  listeners.triggerNoteOff = triggerNoteOff;
}

function getDeviceById(id) {
  var index = connected.findIndex((d) => d.id === id);
  return connected[index];
}

function removeDevice(id) {
  var index = connected.findIndex((d) => d.id === id);
  connected.splice(index, 1);
}

function addMidiListerner(inputDevice) {
  var device = WebMidi.getInputById(inputDevice.id);
  connected.push(device);
  device.addListener('noteon', 'all', function (e) {
    var midi = e.note.number;
    listeners.triggerNoteOn(midi);
  })
  
  device.addListener('noteoff', 'all', function (e) {
    var midi = e.note.number;
    listeners.triggerNoteOff(midi);
  })

  /*
  // add midiCC
  device.addListener('controlchange', 'all', function (e) {
    console.log(`(raw ${e.controller.number}: ${e.value})`, e.controller);
  })
  */
}

WebMidi.enable(function (err) {
  if (!err) {
    setTimeout(function () {
      if (WebMidi.inputs) {
        WebMidi.inputs.forEach(function (input) {
          addMidiListerner(input);
        })
      }
      WebMidi.addListener('connected', function (connectedDevice) {
        var device = connectedDevice;
        if (connectedDevice.port) {
          device = connectedDevice.port;
        }
        if (device.type === 'input') {
          addMidiListerner(device);
        }
      })

      WebMidi.addListener('disconnected', function (disconnected) {
        var device = getDeviceById(disconnected.id);
        if (disconnected.port) {
          device = getDeviceById(disconnected.port.id);
        }
        if (device) {
          device.removeListener('noteon');
          device.removeListener('noteoff');
          removeDevice(disconnected.id);
        }
      })
    }, 100)
  }
})