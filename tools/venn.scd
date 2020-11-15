(
SynthDef(\padSynth, {
	var snd, freq, n;
	freq = \freq.kr(440);
	n = 8;
	snd = { Pulse.ar(freq * (LFNoise2.kr(6) * 0.2).midiratio, LFNoise2.kr(3).range(0.3, 0.7)) } ! n;
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
	snd = snd + NHHall.ar(snd, 3);
	snd = Limiter.ar(snd);
	ReplaceOut.ar(\out.kr(0), snd);
}).add;
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
					envelope = ((midiNote - 60) / 12 / 2).squared.neg.exp;
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
SynthDef(\grainSynth, {
	var snd, freq, ratio;
	freq = \freq.kr(440);
	ratio = LFNoise2.kr(4).range(1, 8).round;
	snd = (LFPulse.ar(freq) - 0.5) * (LFPulse.ar(freq * ratio) - 0.5) * ToggleFF.ar(Dust.ar(4 ! 3));
	snd = Splay.ar(snd);
	snd = snd * Env.asr(0.0, 1, 0.0).ar(Done.freeSelf, \gate.kr(1));
	snd = snd * \amp.kr(0.4);
	Out.ar(\out.kr(0), snd);
}).add;

SynthDef(\grainFx, {
	var snd;
	snd = In.ar(\out.kr(0), 2);
	//snd = snd + NHHall.ar(snd, 3);
	snd = Limiter.ar(snd);
	ReplaceOut.ar(\out.kr(0), snd);
}).add;
)

(
Routine {
	var s = Server.default;
	Synth.tail(nil, \grainFx);
	Server.default.sync;
	loop {
		[0, 2, 3, 5, 7, 8, 10].do { |note|
			var synths;
			s.makeBundle(s.latency, {
				synths = (-4..4).collect { |octave|
					var midiNote, freq, envelope;
					midiNote = 60 + (12 * octave) + note;
					freq = midiNote.midicps;
					envelope = ((midiNote - 44) / 12 / 3).squared.neg.exp;
					Synth(\grainSynth, [
						freq: freq,
						amp: -20.dbamp * envelope,
					]);
				};
			});
			2.wait;
			s.makeBundle(s.latency, {
				synths.do { |synth| synth.set(\gate, 0) };
			});
		};
	};
} .play;
)