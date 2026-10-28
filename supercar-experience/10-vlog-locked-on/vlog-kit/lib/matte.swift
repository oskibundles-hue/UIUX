// matte.swift -- Apple Vision mattes for the SE vlog kit (no model download: the OS ships the models).
//   matte fg     <out_dir> <img...>   foreground instances: <stem>_iN.png (full-res grey mask) + <stem>.json (instance boxes)
//   matte person <out_dir> <img...>   person segmentation (accurate): <stem>_person.png
//   matte people <out_dir> <img...>   person instances (up to 4): <stem>_pN.png + <stem>.json
import Foundation
import Vision
import CoreImage
import ImageIO
import UniformTypeIdentifiers

let args = CommandLine.arguments
guard args.count >= 4 else { print("usage: matte fg|person|people <out_dir> <img...>"); exit(1) }
let mode = args[1], outDir = URL(fileURLWithPath: args[2])
try? FileManager.default.createDirectory(at: outDir, withIntermediateDirectories: true)
let ctx = CIContext(options: [.workingColorSpace: NSNull()])

func writeGray(_ pb: CVPixelBuffer, to url: URL, w: Int, h: Int) {
  var ci = CIImage(cvPixelBuffer: pb)
  let sx = CGFloat(w) / ci.extent.width, sy = CGFloat(h) / ci.extent.height
  if abs(sx - 1) > 1e-3 || abs(sy - 1) > 1e-3 { ci = ci.transformed(by: CGAffineTransform(scaleX: sx, y: sy)) }
  let cs = CGColorSpaceCreateDeviceGray()
  guard let cg = ctx.createCGImage(ci, from: CGRect(x: 0, y: 0, width: w, height: h), format: .L8, colorSpace: cs) else { return }
  let dst = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil)!
  CGImageDestinationAddImage(dst, cg, nil); CGImageDestinationFinalize(dst)
}

for path in args[3...] {
  let url = URL(fileURLWithPath: path)
  let stem = url.deletingPathExtension().lastPathComponent
  guard let src = CGImageSourceCreateWithURL(url as CFURL, nil), let cg = CGImageSourceCreateImageAtIndex(src, 0, nil) else { print("skip", path); continue }
  let W = cg.width, H = cg.height
  let handler = VNImageRequestHandler(cgImage: cg, options: [:])
  do {
    if mode == "person" {
      let r = VNGeneratePersonSegmentationRequest(); r.qualityLevel = .accurate; r.outputPixelFormat = kCVPixelFormatType_OneComponent8
      try handler.perform([r])
      if let o = r.results?.first { writeGray(o.pixelBuffer, to: outDir.appendingPathComponent(stem + "_person.png"), w: W, h: H) }
    } else {
      let r: VNImageBasedRequest = mode == "people" ? VNGeneratePersonInstanceMaskRequest() : VNGenerateForegroundInstanceMaskRequest()
      try handler.perform([r])
      guard let o = r.results?.first as? VNInstanceMaskObservation else { print(stem, "no instances"); continue }
      var info: [[String: Any]] = []
      for i in o.allInstances.sorted() {
        let pb = try o.generateScaledMaskForImage(forInstances: IndexSet(integer: i), from: handler)
        let name = "\(stem)_\(mode == "people" ? "p" : "i")\(i).png"
        writeGray(pb, to: outDir.appendingPathComponent(name), w: W, h: H)
        info.append(["instance": i, "file": name])
      }
      let js = try JSONSerialization.data(withJSONObject: ["w": W, "h": H, "instances": info], options: [.prettyPrinted])
      try js.write(to: outDir.appendingPathComponent(stem + ".json"))
    }
    print("ok", stem, mode)
  } catch { print("ERR", stem, error) }
}
