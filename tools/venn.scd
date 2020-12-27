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
SynthDef(\weirdSynth, {
	var snd, freq, n, auto;
	freq = \freq.kr(440);
	freq = freq * (SinOsc.ar(4 * LFNoise2.kr(3).range(0.9, 1.5) * Line.ar(0, 1, 0.5), Rand(0, 2pi)) * 0.1 * Line.ar(0, 1, 0.5)).midiratio;
	n = 2;
	snd = Pulse.ar(freq, 0.9);
	auto = Line.kr(0, 1, 2);
	snd = (RLPF.ar(snd, [
		500 * (auto * 12).neg.midiratio,
		1140 * (auto * 12).midiratio,
		2501 * (auto * 5).midiratio,
	] * Rand(0.9, 1.2), 0.1) * [0, -5, -10].dbamp).sum;
	snd = Splay.ar(snd, 0.5);
	snd = LPF.ar(snd, (freq * 5).min(16e3));
	snd = snd * Env.asr(0.1, 1, 0.1).ar(Done.freeSelf, \gate.kr(1));
	snd = snd * \amp.kr(0.4);
	Out.ar(\out.kr(0), snd);
}).add;

SynthDef(\weirdFx, {
	var snd;
	snd = In.ar(\out.kr(0), 2);
	snd = BPeakEQ.ar(snd, 2000, 1, -3);
	snd = LeakDC.ar(snd);
	snd = Limiter.ar(snd);
	snd = snd + NHHall.ar(snd, 1, earlyDiffusion: 0.9, lateDiffusion: 0.9);
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
			Synth(\weirdSynth, [
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

~recordPath = "../app/sounds/weird/".resolveRelative;
"mkdir -p %".format(~recordPath).unixCmd;

Routine {
	var s = Server.default;
	Synth.tail(nil, \weirdFx);
	[0, 2, 3, 5, 7, 8, 10].do { |note|
		s.sync;
		s.recHeaderFormat = "WAV";
		s.prepareForRecord(~recordPath +/+ "note_%.wav".format(note));
		s.sync;
		s.record;
		~play.(note);
		// Hack because we may receive premature triggers before start of note.
		1.0.wait;
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
SynthDef(\reedSynth, {
	var snd, freq, n, auto;
	freq = \freq.kr(440);
	freq = freq * (Rand(-1, 1) * 0.03).midiratio * (LFNoise2.kr(3) * 0.05).midiratio;
	snd = Pulse.ar(freq, LFNoise2.kr(3).linexp(-1, 1, 0.7, 0.9)) ! 2;
	snd = LPF.ar(snd, XLine.kr(3000, 8000, 0.1));
	snd = snd + (snd > 0 * HPF.ar(PinkNoise.ar, 3000) * 2.dbamp);
	snd = snd * Env.asr(0.1, 1, freq.explin(100, 8000, 0.3, 0.1)).ar(Done.freeSelf, \gate.kr(1));
	snd = snd * \amp.kr(0.4);
	Out.ar(\out.kr(0), snd);
}).add;

SynthDef(\reedFx, {
	var snd;
	snd = In.ar(\out.kr(0), 2);
	snd = BPeakEQ.ar(snd, 2000, 1, -3);
	snd = LeakDC.ar(snd);
	snd = Limiter.ar(snd);
	snd = snd + NHHall.ar(snd, 1, earlyDiffusion: 0.9, lateDiffusion: 0.9);
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
			Synth(\reedSynth, [
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

~recordPath = "../app/sounds/reed/".resolveRelative;
"mkdir -p %".format(~recordPath).unixCmd;

Routine {
	var s = Server.default;
	Synth.tail(nil, \reedFx);
	[0, 2, 3, 5, 7, 8, 10].do { |note|
		s.sync;
		s.recHeaderFormat = "WAV";
		s.prepareForRecord(~recordPath +/+ "note_%.wav".format(note));
		s.sync;
		s.record;
		~play.(note);
		// Hack because we may receive premature triggers before start of note.
		1.0.wait;
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
SynthDef(\dropletSynth, {
	var snd, freq, n, auto, trig;
	freq = \freq.kr(440);
	trig = Dust2.ar(1 ! 4);
	snd = SinOsc.ar(freq * TIRand.ar(1, 4, trig)) * Decay2.ar(trig, 0.05, 0.2) * 500;
	snd = SinOsc.ar(freq + snd) * Decay2.ar(trig, 0.01, 0.3);
	snd = Splay.ar(snd, 0.5);
	snd = snd * 10.dbamp;
	snd = snd * Env.asr(0.1, 1, 0.1).ar(Done.freeSelf, \gate.kr(1));
	snd = snd * \amp.kr(0.4);
	Out.ar(\out.kr(0), snd);
}).add;

SynthDef(\dropletFx, {
	var snd;
	snd = In.ar(\out.kr(0), 2);
	snd = LeakDC.ar(snd);
	snd = Limiter.ar(snd);
	snd = snd + NHHall.ar(snd, 1, earlyDiffusion: 0.9, lateDiffusion: 0.9);
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
			envelope = ((midiNote - 72) / 12 / 2).squared.neg.exp;
			Synth(\dropletSynth, [
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

~recordPath = "../app/sounds/droplet/".resolveRelative;
"mkdir -p %".format(~recordPath).unixCmd;

Routine {
	var s = Server.default;
	Synth.tail(nil, \dropletFx);
	[0, 2, 3, 5, 7, 8, 10].do { |note|
		s.sync;
		s.recHeaderFormat = "WAV";
		s.prepareForRecord(~recordPath +/+ "note_%.wav".format(note));
		s.sync;
		s.record;
		~play.(note);
		// Hack because we may receive premature triggers before start of note.
		1.0.wait;
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
SynthDef(\pianoSynth, {
	var snd, freq, n;
	freq = \freq.kr(440) * [-0.03, 0, 0.03].midiratio;
	snd = SinOsc.ar(freq + (SinOsc.ar(freq * 2) * Env.perc(0.01, 3.25).ar * 500));
	snd = snd + (SinOsc.ar(freq + (SinOsc.ar(freq * 7.5) * Env.perc(0.01, 1.25).ar * 500)) * Env.perc(0.001, 0.05).ar);
	snd = Splay.ar(snd, 0.5);
	snd = snd * Env.perc(0.01, freq.explin(100, 8000, 5, 3)).ar(Done.freeSelf);
	snd = snd * \amp.kr(0.4);
	Out.ar(\out.kr(0), snd);
}).add;

SynthDef(\pianoFx, {
	var snd;
	snd = In.ar(\out.kr(0), 2);
	snd = LeakDC.ar(snd);
	snd = Limiter.ar(snd);
	snd = snd * (0.75 + (0.25 * SinOsc.ar(4, [0, pi])));
	snd = snd + NHHall.ar(snd, 1, earlyDiffusion: 0.9, lateDiffusion: 0.9);
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
			envelope = ((midiNote - 60) / 12 / 2).squared.neg.exp;
			Synth(\pianoSynth, [
				freq: freq,
				amp: -20.dbamp * envelope,
			]);
		};
	});
	5.wait;
};

~recordPath = "../app/sounds/piano/".resolveRelative;
"mkdir -p %".format(~recordPath).unixCmd;

Routine {
	var s = Server.default;
	Synth.tail(nil, \pianoFx);
	[0, 2, 3, 5, 7, 8, 10].do { |note|
		s.sync;
		s.recHeaderFormat = "WAV";
		s.prepareForRecord(~recordPath +/+ "note_%.wav".format(note));
		s.sync;
		s.record;
		~play.(note);
		// Hack because we may receive premature triggers before start of note.
		1.0.wait;
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
SynthDef(\bell2Synth, {
	var snd, freq, n;
	freq = \freq.kr(440);
	snd = Saw.ar(freq * (SinOsc.ar(4) * Line.kr(0, 1, 1) * 0.25).midiratio);
	snd = MoogFF.ar(snd, Env.perc(Rand(0.1, 0.9), Rand(3.0, 4.0)).ar.linexp(0, 1, 1, 8) * freq, 3.5);
	snd = (snd * 5.dbamp).tanh * 10.dbamp;
	snd = snd ! 2;
	snd = snd * Env.perc(0.01, 5.0).ar(Done.freeSelf);
	snd = snd * \amp.kr(0.4);
	Out.ar(\out.kr(0), snd);
}).add;

SynthDef(\bell2Fx, {
	var snd;
	snd = In.ar(\out.kr(0), 2);
	snd = LeakDC.ar(snd);
	snd = Limiter.ar(snd);
	snd = snd + NHHall.ar(snd, 1, earlyDiffusion: 0.9, lateDiffusion: 0.9);
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
			envelope = ((midiNote - 60) / 12 / 2).squared.neg.exp;
			Synth(\bell2Synth, [
				freq: freq,
				amp: -20.dbamp * envelope,
			]);
		};
	});
	5.wait;
};

~recordPath = "../app/sounds/bell2/".resolveRelative;
"mkdir -p %".format(~recordPath).unixCmd;

Routine {
	var s = Server.default;
	Synth.tail(nil, \bell2Fx);
	[0, 2, 3, 5, 7, 8, 10].do { |note|
		s.sync;
		s.recHeaderFormat = "WAV";
		s.prepareForRecord(~recordPath +/+ "note_%.wav".format(note));
		s.sync;
		s.record;
		~play.(note);
		// Hack because we may receive premature triggers before start of note.
		1.0.wait;
		OSCFunc({
			s.stopRecording;
		}, \done).oneShot;
		while { s.isRecording } {
			1.0.wait;
		};
	};
} .play;
)