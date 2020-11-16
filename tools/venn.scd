/*

Sorry about the code duplication and general disorderliness of this file.

*/

(
SynthDef(\padSynth, {
	var snd, freq, n;
	freq = \freq.kr(440);
	n = 8;
	snd = { Saw.ar(freq * (LFNoise2.kr(2) * 0.15).midiratio) * 6.dbamp } ! n;
	snd = RLPF.ar(snd, freq * 3 * (LFNoise2.kr(3 ! n) * 12).midiratio, 0.5);
	snd = Splay.ar(snd);
	snd = LPF.ar(snd, (freq * 5).min(16e3));
	snd = snd * Env.asr(3, 1, 3).ar(Done.freeSelf, \gate.kr(1));
	snd = snd * \amp.kr(0.4);
	Out.ar(\out.kr(0), snd);
}).add;

SynthDef(\padFx, {
	var snd;
	snd = In.ar(\out.kr(0), 2);
	snd = BPeakEQ.ar(snd, 4000, 1, -3);
	snd = snd + (NHHall.ar(snd, 3) * -10.dbamp);
	snd = Limiter.ar(snd);
	SendReply.ar(Trig1.ar(DetectSilence.ar(snd.abs.sum), SampleDur.ir), '/done');
	ReplaceOut.ar(\out.kr(0), snd);
}).add;
)


(
~play = { |note|
	var s = Server.default;
	var synths;
	s.makeBundle(s.latency, {
		synths = (-4..4).collect { |octave|
			var midiNote, freq, envelope;
			midiNote = 60 + (12 * octave) + note;
			freq = midiNote.midicps;
			envelope = ((midiNote - 54) / 12 / 2).squared.neg.exp;
			Synth(\padSynth, [
				freq: freq,
				amp: -20.dbamp * envelope,
			]);
		};
	});
	5.wait;
	s.makeBundle(s.latency, {
		synths.do { |synth| synth.set(\gate, 0) };
	});
};

~recordPath = "../app/sounds/pad/".resolveRelative;
"mkdir -p %".format(~recordPath).unixCmd;

Routine {
	var s = Server.default;
	Synth.tail(nil, \padFx);
	[0, 2, 3, 5, 7, 8, 10].do { |note|
		s.sync;
		s.recHeaderFormat = "WAV";
		s.prepareForRecord(~recordPath +/+ "note_%.wav".format(note));
		s.sync;
		s.record;
		~play.(note);
		// Hack because we may receive premature triggers before start of note.
		3.0.wait;
		OSCFunc({
			s.stopRecording;
		}, \done).oneShot;
		while { s.isRecording } {
			1.0.wait;
		};
	};
} .play;
)

(
Routine {
	var s = Server.default;
	Synth.tail(nil, \padFx);
	Server.default.sync;
	loop {
		[0, 2, 3, 5, 7, 8, 10].do { |note|
			var synths;
			s.makeBundle(s.latency, {
				synths = (-4..4).collect { |octave|
					var midiNote, freq, envelope;
					midiNote = 60 + (12 * octave) + note;
					freq = midiNote.midicps;
					envelope = ((midiNote - 54) / 12 / 2).squared.neg.exp;
					Synth(\padSynth, [
						freq: freq,
						amp: -20.dbamp * envelope,
					]);
				};
			});
			5.wait;
			s.makeBundle(s.latency, {
				synths.do { |synth| synth.set(\gate, 0) };
			});
		};
	};
} .play;
)



(
SynthDef(\bellSynth, {
	var snd, freq, n, count;
	freq = \freq.kr(440) * XLine.kr(2, 1, 0.005);
	count = 8;
	n = (1..count);
	snd = SinOsc.ar(freq * n * (1 + (n * n * freq.explin(100, 8000, 1.5e-3, 0.5e-3))).sqrt);
	snd = snd * Env.perc({ ExpRand(0.005, 0.05) } ! count, 8.0 * (n.reciprocal ** 1.3)).ar;
	snd = snd.sum;
	snd = snd * -10.dbamp;
	snd = snd ! 2;
	snd = snd * Env.perc(0.001, 4.0).ar(Done.freeSelf);
	snd = snd * \amp.kr(0.4);
	Out.ar(\out.kr(0), snd);
}).add;

SynthDef(\bellFx, {
	var snd;
	snd = In.ar(\out.kr(0), 2);
	snd = BPeakEQ.ar(snd, 4000, 1, -12);
	snd = snd + NHHall.ar(snd, 1, earlyDiffusion: 0.9, lateDiffusion: 0.9);
	snd = Limiter.ar(snd);
	SendReply.ar(Trig1.ar(DetectSilence.ar(snd.abs.sum), SampleDur.ir), '/done');
	ReplaceOut.ar(\out.kr(0), snd);
}).add;
)

(
~play = { |note|
	var s = Server.default;
	s.makeBundle(s.latency, {
		(-4..4).collect { |octave|
			var midiNote, freq, envelope;
			midiNote = 60 + (12.08 * (octave + (note / 12)));
			freq = midiNote.midicps;
			envelope = ((midiNote - 66) / 12 / 2).squared.neg.exp;
			Synth(\bellSynth, [
				freq: freq,
				amp: -20.dbamp * envelope,
			]);
		};
	});
};

~recordPath = "/home/nathan/tmp/";

Routine {
	var s = Server.default;
	Synth.tail(nil, \bellFx);
	[0, 2, 3, 5, 7, 8, 10].do { |note|
		s.sync;
		s.recHeaderFormat = "WAV";
		s.prepareForRecord(~recordPath +/+ "note_%.wav".format(note));
		s.sync;
		s.record;
		~play.(note);
		// Hack because we may receive premature triggers before start of note.
		3.0.wait;
		OSCFunc({
			s.stopRecording;
		}, \done).oneShot;
		while { s.isRecording } {
			1.0.wait;
		};
	};
} .play;
)

(
Routine {
	var s = Server.default;
	Synth.tail(nil, \bellFx);
	Server.default.sync;
	loop {
		[0, 2, 3, 5, 7, 8, 10].do { |note|
			var synths;
			s.makeBundle(s.latency, {
				synths = (-4..4).collect { |octave|
					var midiNote, freq, envelope;
					midiNote = 60 + (12.08 * (octave + (note / 12)));
					freq = midiNote.midicps;
					envelope = ((midiNote - 66) / 12 / 2).squared.neg.exp;
					Synth(\bellSynth, [
						freq: freq,
						amp: -20.dbamp * envelope,
					]);
				};
			});
			1.wait;
		};
	};
} .play;
)




(
SynthDef(\alienSynth, {
	var snd, freq, n;
	freq = \freq.kr(440);
	n = 2;
	snd = Saw.ar(freq * (LFNoise2.kr(3 ! n) * 0.1).midiratio);
	snd = MoogFF.ar(snd, (freq * TRand.kr(1, 8, Dust.kr(8 ! n))).min(16e3), 3.5);
	snd = snd * 20.dbamp;
	snd = Splay.ar(snd, 0.3);
	snd = snd * Env.asr(0.01, 1, 0.01).ar(Done.freeSelf, \gate.kr(1));
	snd = snd * \amp.kr(0.4);
	Out.ar(\out.kr(0), snd);
}).add;

SynthDef(\alienFx, {
	var snd, wet;
	snd = In.ar(\out.kr(0), 2);
	snd = LeakDC.ar(snd);
	snd = BPeakEQ.ar(snd, 4000, 1, -3);
	wet = snd + LocalIn.ar(2);
	wet = DelayC.ar(wet, 2, 1 + (SinOsc.ar(0.5, [0, pi]) * 1e-4));
	wet = wet * -10.dbamp;
	wet = wet + PitchShift.ar(wet, 0.2, 2);
	wet = wet + PitchShift.ar(wet, 0.2, 0.5);
	wet = LPF.ar(wet, 4000);
	wet = HPF.ar(wet, 100);
	LocalOut.ar(wet);
	snd = snd + wet;
	snd = LeakDC.ar(snd);
	snd = Limiter.ar(snd);
	SendReply.ar(Trig1.ar(DetectSilence.ar(snd.abs.sum, -60.dbamp), SampleDur.ir), '/done');
	ReplaceOut.ar(\out.kr(0), snd);
}).add;
)

(
Routine {
	var s = Server.default;
	Synth.tail(nil, \alienFx);
	Server.default.sync;
	loop {
		[0, 2, 3, 5, 7, 8, 10].do { |note|
			var synths;
			s.makeBundle(s.latency, {
				synths = (-4..4).collect { |octave|
					var midiNote, freq, envelope;
					midiNote = 60 + (12 * octave) + note;
					freq = midiNote.midicps;
					envelope = ((midiNote - 54) / 12 / 2).squared.neg.exp;
					Synth(\alienSynth, [
						freq: freq,
						amp: -20.dbamp * envelope,
					]);
				};
			});
			5.wait;
			s.makeBundle(s.latency, {
				synths.do { |synth| synth.set(\gate, 0) };
			});
		};
	};
} .play;
)

(
~play = { |note|
	var s = Server.default;
	var synths;
	s.makeBundle(s.latency, {
		synths = (-4..4).collect { |octave|
			var midiNote, freq, envelope;
			midiNote = 60 + (12 * octave) + note;
			freq = midiNote.midicps;
			envelope = ((midiNote - 54) / 12 / 2).squared.neg.exp;
			Synth(\alienSynth, [
				freq: freq,
				amp: -20.dbamp * envelope,
			]);
		};
	});
	5.wait;
	s.makeBundle(s.latency, {
		synths.do { |synth| synth.set(\gate, 0) };
	});
};

~recordPath = "../app/sounds/alien/".resolveRelative;
"mkdir -p %".format(~recordPath).unixCmd;

Routine {
	var s = Server.default;
	Synth.tail(nil, \alienFx);
	[0, 2, 3, 5, 7, 8, 10].do { |note|
		s.sync;
		s.recHeaderFormat = "WAV";
		s.prepareForRecord(~recordPath +/+ "note_%.wav".format(note));
		s.sync;
		s.record;
		~play.(note);
		// Hack because we may receive premature triggers before start of note.
		3.0.wait;
		OSCFunc({
			s.stopRecording;
		}, \done).oneShot;
		while { s.isRecording } {
			1.0.wait;
		};
	};
} .play;
)